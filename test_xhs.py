#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试小红书页面结构
"""
import time
from scrapling.fetchers import StealthySession

# 测试URL
url = "https://www.xiaohongshu.com/search_result?keyword=%E4%B8%80%E5%8A%A0turbo6&source=web_explore_feed"

print("开始测试访问小红书页面...")

with StealthySession(
    headless=False,
    solve_cloudflare=True,
    timeout=60000,
    block_images=False,
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
) as session:
    try:
        # 先访问小红书主页
        print("访问小红书主页...")
        session.fetch("https://www.xiaohongshu.com", google_search=False)
        time.sleep(3)
        
        # 然后访问搜索页面
        print("访问搜索页面...")
        page = session.fetch(
            url,
            wait_for_timeout=10000,
            google_search=False,
        )
        
        print(f"状态码: {page.status}")
        print(f"页面标题: {page.css('title::text').get()}")
        
        # 打印页面的一部分来查看结构
        print("\n页面前2000字符:")
        print(page.text[:2000])
        
        # 查找所有可能的笔记元素
        print("\n查找笔记元素...")
        
        # 尝试不同的选择器
        selectors_to_try = [
            ".note-item",
            ".note-card",
            ".feed-item",
            ".card",
            '[data-id]',
            '[data-note-id]',
            'a[href*="/note/"]',
        ]
        
        for selector in selectors_to_try:
            elements = page.css(selector)
            print(f"选择器 '{selector}': 找到 {len(elements)} 个元素")
        
        # 查找所有链接
        print("\n查找笔记链接...")
        links = page.css('a::attr(href)').getall()
        note_links = [link for link in links if link and '/note/' in link]
        print(f"找到 {len(note_links)} 个笔记链接")
        for link in note_links[:10]:
            print(f"  - {link}")
        
        # 保存完整页面
        with open("xhs_page.html", "w", encoding="utf-8") as f:
            f.write(page.text)
        print("\n页面已保存到 xhs_page.html")
        
    except Exception as e:
        print(f"出错: {e}")
        import traceback
        traceback.print_exc()
