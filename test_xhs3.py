#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试小红书页面结构 - 使用 page_action
"""
import time
from scrapling.fetchers import StealthySession

# 测试URL
url = "https://www.xiaohongshu.com/search_result?keyword=%E4%B8%80%E5%8A%A0turbo6&source=web_explore_feed"

print("开始测试访问小红书页面...")

# 用于存储页面数据
page_data = {}

def extract_info(page):
    """在页面上执行的操作"""
    print("执行 page_action...")
    
    # 等待页面加载
    page.wait_for_timeout(5000)
    
    # 滚动页面
    for i in range(3):
        print(f"滚动页面 {i+1}/3")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
    
    # 获取HTML
    html = page.content()
    page_data["html"] = html
    page_data["title"] = page.title()
    
    # 查找笔记链接
    links = page.locator("a").all()
    note_links = []
    for link in links:
        try:
            href = link.get_attribute("href")
            if href and "/note/" in href:
                note_links.append(href)
        except:
            pass
    page_data["note_links"] = note_links
    
    # 查找图片
    images = page.locator("img").all()
    image_urls = []
    for img in images:
        try:
            src = img.get_attribute("src")
            if src and ("sns" in src or "xiaohongshu" in src or "xhs" in src):
                image_urls.append(src)
        except:
            pass
    page_data["images"] = image_urls
    
    # 查找所有元素的class
    classes = page.evaluate("""() => {
        const allClasses = new Set();
        document.querySelectorAll('[class]').forEach(el => {
            el.classList.forEach(cls => allClasses.add(cls));
        });
        return Array.from(allClasses).slice(0, 100);
    }""")
    page_data["classes"] = classes
    
    print(f"page_action 完成，找到 {len(note_links)} 个笔记链接")

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
            page_action=extract_info,
            wait=3000,
        )
        
        print(f"\n状态码: {page.status}")
        print(f"页面标题: {page_data.get('title')}")
        print(f"HTML长度: {len(page_data.get('html', ''))}")
        
        print("\n笔记链接:")
        for link in page_data.get("note_links", [])[:20]:
            print(f"  - {link}")
        
        print(f"\n找到 {len(page_data.get('note_links', []))} 个笔记链接")
        
        print("\n图片URL (前20个):")
        for img in page_data.get("images", [])[:20]:
            print(f"  - {img[:100]}...")
        
        print(f"\n找到 {len(page_data.get('images', []))} 张图片")
        
        print("\n页面中的class (前50个):")
        for cls in page_data.get("classes", [])[:50]:
            if "item" in cls.lower() or "card" in cls.lower() or "note" in cls.lower() or "feed" in cls.lower():
                print(f"  - {cls}")
        
        # 保存页面
        with open("xhs_page3.html", "w", encoding="utf-8") as f:
            f.write(page_data.get("html", ""))
        print("\n页面已保存到 xhs_page3.html")
        
        # 尝试用选择器查找
        print("\n尝试用选择器查找元素...")
        classes = page_data.get("classes", [])
        for cls in classes:
            if "item" in cls.lower() or "card" in cls.lower() or "note" in cls.lower():
                elements = page.css(f".{cls}")
                if len(elements) > 0:
                    print(f"  .{cls}: {len(elements)} 个元素")
        
    except Exception as e:
        print(f"出错: {e}")
        import traceback
        traceback.print_exc()
