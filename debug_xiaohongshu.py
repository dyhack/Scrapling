#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本：查看小红书页面内容
"""

from scrapling.fetchers import StealthySession
import time

def debug_page():
    """调试小红书页面"""
    with StealthySession(
        headless=False,
        solve_cloudflare=True,
        network_idle=True,
        timeout=60
    ) as session:
        url = "https://www.xiaohongshu.com/search_result?keyword=%E4%B8%80%E5%8A%A0turbo6&source=web_explore_feed"
        print(f"访问: {url}")
        
        page = session.fetch(url, google_search=True)
        print(f"状态码: {page.status}")
        
        # 等待页面加载
        time.sleep(5)
        
        # 获取页面HTML
        html = str(page)
        print(f"\n页面内容长度: {len(html)} 字符")
        
        # 保存完整HTML
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("完整HTML已保存到 debug_page.html")
        
        # 打印前2000字符预览
        print("\n" + "="*60)
        print("页面内容预览:")
        print("="*60)
        print(html[:2000])
        print("...")
        
        # 查找所有链接
        print("\n" + "="*60)
        print("页面中的链接:")
        print("="*60)
        links = page.css('a')
        for i, link in enumerate(links[:20], 1):
            href = link.attrib.get('href', 'N/A')
            text = link.css('::text').get() or ''
            print(f"{i:2d}. href: {href[:60]}")
            if text.strip():
                print(f"    文本: {text.strip()[:40]}")
        
        # 搜索note相关的内容
        print("\n" + "="*60)
        print("包含'note'的链接:")
        print("="*60)
        for link in links:
            href = link.attrib.get('href', '')
            if 'note' in href.lower():
                print(f"  - {href}")
        
        # 检查页面中是否有script标签包含数据
        print("\n" + "="*60)
        print("script标签中的数据:")
        print("="*60)
        scripts = page.css('script')
        for i, script in enumerate(scripts[:5], 1):
            script_text = script.css('::text').get() or ''
            if 'note' in script_text.lower() or 'image' in script_text.lower():
                print(f"脚本 {i}: 包含相关数据 (长度: {len(script_text)})")
                if len(script_text) > 500:
                    print(f"  预览: {script_text[:200]}...")

if __name__ == "__main__":
    debug_page()
