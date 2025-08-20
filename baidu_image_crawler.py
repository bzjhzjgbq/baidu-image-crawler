#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
百度图片爬虫
用法: python baidu_image_crawler.py [关键词] [数量]
"""

# ========== 标准库 ==========
import os
import sys
import time
import random

# ========== 第三方库 ==========
import requests
from concurrent.futures import ThreadPoolExecutor

# ========== Selenium生态 ==========
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# 参数设置
keyword = sys.argv[1] if len(sys.argv) > 1 else 'image'
count = int(sys.argv[2]) if len(sys.argv) > 2 else 100
folder = keyword
if not os.path.exists(folder): os.makedirs(folder)

# 初始化浏览器
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124")
try:
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
except:
    driver = webdriver.Chrome(options=options)

# 下载函数
def download(url, path):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://image.baidu.com/'}, timeout=10)
        if r.status_code == 200:
            with open(path, 'wb') as f: f.write(r.content)
            return True
    except: pass
    return False

try:
    # 搜索图片
    print(f"搜索: {keyword}, 目标: {count}张")
    driver.get('https://image.baidu.com/')
    time.sleep(2)
    
    # 输入关键词搜索
    for s in ['#kw', 'input[name="word"]', '.s_ipt']:
        try:
            box = driver.find_element(By.CSS_SELECTOR, s)
            box.send_keys(keyword + Keys.RETURN)
            break
        except: continue
    time.sleep(2)
    
    # 下载图片
    downloaded = set()
    total = 0
    
    while total < count:
        # 查找图片
        images = []
        for s in ['.main_img', '.imgitem img', 'img.main_img']:
            try:
                found = driver.find_elements(By.CSS_SELECTOR, s)
                if found: 
                    images = found
                    break
            except: pass
        
        if not images:
            images = driver.find_elements(By.TAG_NAME, 'img')
        
        if not images:
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(1)
            continue
        
        # 随机处理图片
        random.shuffle(images)
        tasks = []
        
        for img in images:
            if total >= count: break
            try:
                src = img.get_attribute('src') or img.get_attribute('data-src')
                if not src or not src.startswith('http') or src in downloaded: continue
                
                path = os.path.join(folder, f"{total+1}.jpeg")
                tasks.append((src, path))
                downloaded.add(src)
                total += 1
            except: continue
        
        # 并行下载
        if tasks:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(download, url, path) for url, path in tasks]
                success = sum(1 for f in futures if f.result())
                print(f"已下载: {total}张, 本批成功: {success}张")
        
        # 滚动加载更多
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(1)

except KeyboardInterrupt:
    print("用户中断")
except Exception as e:
    print(f"错误: {e}")
finally:
    print(f"\n下载完成: 目标{count}张, 实际下载{total if 'total' in locals() else 0}张")
    driver.quit()
    
    # 打开图片文件夹
    if os.name == 'nt':
        try: os.system(f'explorer "{os.path.abspath(folder)}"')
        except: pass
