#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试小红书页面结构 - 等待内容加载
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
        # 访问搜索页面
        print("访问搜索页面...")
        page = session.fetch(
            url,
            google_search=False,
        )
        
        print(f"状态码: {page.status}")
        print(f"页面标题: {page.css('title::text').get()}")
        
        # 使用 Playwright 页面对象等待内容加载
        print("等待页面内容加载...")
        pw_page = session.page
        
        # 等待并滚动页面
        for i in range(5):
            print(f"等待... {i+1}/5")
            pw_page.wait_for_timeout(2000)
            # 向下滚动
            pw_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        
        # 等待一段时间
        pw_page.wait_for_timeout(3000)
        
        # 获取HTML内容
        html = pw_page.content()
        
        print("\n页面内容长度:", len(html))
        print("\n页面前3000字符:")
        print(html[:3000])
        
        # 查找笔记相关的内容
        print("\n检查页面中是否有笔记数据...")
        
        # 检查是否有 script 标签包含数据
        scripts = pw_page.locator("script").all()
        print(f"找到 {len(scripts)} 个script标签")
        
        for i, script in enumerate(scripts[:10]):
            try:
                content = script.inner_html()
                if "note" in content.lower() or "item" in content.lower() or "image" in content.lower():
                    if len(content) > 100:
                        print(f"\nScript {i} 包含数据: {content[:500]}...")
            except:
                pass
        
        # 查找所有包含 note 的元素
        print("\n查找包含 note 的元素:")
        elements = pw_page.locator('[class*="note"]').all()
        print(f"找到 {len(elements)} 个包含 note 的元素")
        
        # 查找所有链接
        print("\n查找所有链接...")
        links = pw_page.locator("a").all()
        print(f"找到 {len(links)} 个链接")
        
        note_links = []
        for link in links[:50]:
            try:
                href = link.get_attribute("href")
                if href and "/note/" in href:
                    note_links.append(href)
                    print(f"  - 笔记链接: {href}")
            except:
                pass
        
        print(f"\n总共找到 {len(note_links)} 个笔记链接")
        
        # 查找图片
        print("\n查找图片...")
        images = pw_page.locator("img").all()
        print(f"找到 {len(images)} 张图片")
        for img in images[:20]:
            try:
                src = img.get_attribute("src")
                alt = img.get_attribute("alt")
                if src and ("sns" in src or "xiaohongshu" in src):
                    print(f"  - 图片: {src[:100]}... alt: {alt}")
            except:
                pass
        
        # 保存完整页面
        with open("xhs_page2.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("\n页面已保存到 xhs_page2.html")
        
    except Exception as e:
        print(f"出错: {e}")
        import traceback
        traceback.print_exc()
