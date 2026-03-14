#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试小红书搜索 - 修复重定向和链接提取问题
"""
import time
import re
from scrapling.fetchers import StealthySession

# 测试URL - 使用完整的URL
url = "https://www.xiaohongshu.com/search_result?keyword=%E4%B8%80%E5%8A%A0turbo6&source=web_explore_feed&m_source=itab"

print("开始测试访问小红书搜索页面...")
print(f"URL: {url}")

page_data = {}

def extract_info(page):
    """在页面上执行的操作"""
    print("执行 page_action...")
    print(f"当前页面URL: {page.url}")
    
    # 等待页面加载
    page.wait_for_timeout(8000)
    
    # 打印页面标题
    print(f"页面标题: {page.title()}")
    
    # 检查是否被重定向
    if "search_result" not in page.url:
        print(f"警告: 页面被重定向到: {page.url}")
        
        # 尝试手动访问搜索
        print("尝试在页面内执行搜索...")
        try:
            # 查找搜索框
            search_input = page.locator("input[type='search'], input[placeholder*='搜索']")
            if search_input.count() > 0:
                print("找到搜索框，尝试输入搜索词...")
                search_input.first.fill("一加turbo6")
                search_input.first.press("Enter")
                page.wait_for_timeout(5000)
                print(f"搜索后URL: {page.url}")
        except Exception as e:
            print(f"搜索尝试失败: {e}")
    
    # 处理cookie和弹窗
    try:
        cookie_btns = page.locator("button:has-text('同意'), button:has-text('接受'), div[class*='cookie'] button")
        if cookie_btns.count() > 0:
            cookie_btns.first.click(timeout=1000)
            print("点击了cookie同意按钮")
            page.wait_for_timeout(1000)
    except:
        pass
    
    try:
        close_btns = page.locator("svg[class*='close'], div[class*='close']:visible, button[aria-label='关闭']:visible")
        if close_btns.count() > 0:
            close_btns.first.click(timeout=1000)
            print("关闭了弹窗")
    except:
        pass
    
    # 滚动加载内容
    print("滚动加载内容...")
    for i in range(3):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
    
    # 查找所有笔记链接 - 使用正则匹配探索页的笔记
    print("\n=== 查找所有笔记链接 ===")
    
    # 查找explore链接
    explore_links = page.evaluate("""() => {
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            const href = a.getAttribute('href');
            if (href && href.match(/\\/explore\\/[0-9a-f]{16,}/)) {
                links.push({
                    href: href,
                    text: a.textContent?.substring(0, 50),
                    classes: a.className
                });
            }
        });
        return links;
    }""")
    
    print(f"找到explore链接: {len(explore_links)}")
    for link in explore_links[:10]:
        print(f"  - {link['href']}")
    
    # 查找包含xsec_token的链接
    xsec_links = page.evaluate("""() => {
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            const href = a.getAttribute('href');
            if (href && href.includes('xsec_token')) {
                links.push(href);
            }
        });
        return links;
    }""")
    
    print(f"\n包含xsec_token的链接: {len(xsec_links)}")
    for link in xsec_links[:10]:
        print(f"  - {link[:100]}...")
    
    # 检查note-item
    note_items = page.evaluate("""() => {
        const items = [];
        document.querySelectorAll('.note-item, [class*="card"], [class*="feed"]').forEach(el => {
            const links = el.querySelectorAll('a');
            const img = el.querySelector('img');
            if (links.length > 0) {
                items.push({
                    links: Array.from(links).map(a => a.getAttribute('href')).filter(h => h),
                    img: img?.getAttribute('src'),
                    classes: el.className
                });
            }
        });
        return items.slice(0, 10);
    }""")
    
    print(f"\n找到笔记项: {len(note_items)}")
    for i, item in enumerate(note_items):
        print(f"\n笔记项 {i}:")
        print(f"  classes: {item['classes']}")
        print(f"  links: {item['links'][:3]}")
        if item['img']:
            print(f"  img: {item['img'][:80]}...")
    
    # 保存数据
    page_data["explore_links"] = explore_links
    page_data["xsec_links"] = xsec_links
    page_data["note_items"] = note_items
    page_data["html"] = page.content()
    page_data["url"] = page.url
    page_data["title"] = page.title()

with StealthySession(
    headless=False,
    solve_cloudflare=True,
    timeout=120000,
    block_images=False,
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
) as session:
    try:
        page = session.fetch(
            url,
            google_search=False,
            page_action=extract_info,
            wait=5000,
        )
        
        print(f"\n=== 最终结果 ===")
        print(f"状态码: {page.status}")
        print(f"最终URL: {page_data.get('url')}")
        print(f"页面标题: {page_data.get('title')}")
        
        # 使用Scrapling的CSS选择器
        print("\n=== 使用Scrapling CSS选择器 ===")
        
        # 方法1: 使用 ::attr(href) 伪元素
        all_hrefs = page.css("a::attr(href)").getall()
        print(f"页面总链接数: {len(all_hrefs)}")
        
        # 提取笔记链接
        note_urls = []
        for href in all_hrefs:
            if href:
                # 检查是否是笔记链接
                if re.search(r'/explore/[0-9a-f]{16,}', href) or re.search(r'/note/\d+', href):
                    note_urls.append(href)
                elif 'xsec_token' in href:
                    note_urls.append(href)
        
        print(f"找到笔记URL: {len(note_urls)}")
        for url in note_urls[:20]:
            print(f"  - {url}")
        
        # 方法2: 使用 .attrib 属性
        print("\n=== 使用 .attrib 属性获取 ===")
        all_links = page.css("a")
        note_urls2 = []
        for link in all_links:
            href = link.attrib.get('href')
            if href and (re.search(r'/explore/[0-9a-f]{16,}', href) or 'xsec_token' in href):
                note_urls2.append(href)
        print(f"使用.attrib找到笔记URL: {len(note_urls2)}")
        
        # 查找note-item中的图片
        print("\n=== 查找笔记图片 ===")
        img_srcs = page.css(".note-item img::attr(src)").getall()
        print(f".note-item下的图片数: {len(img_srcs)}")
        for src in img_srcs[:10]:
            if src:
                print(f"  - {src[:100]}...")
        
        # 保存页面
        with open("xhs_page5.html", "w", encoding="utf-8") as f:
            f.write(page_data.get("html", ""))
        print(f"\n页面已保存到 xhs_page5.html")
        
        # 分析问题: 为什么没有跳转到搜索结果页?
        print("\n=== 问题分析 ===")
        if "search_result" not in page_data.get("url", ""):
            print("⚠️  问题: 搜索页面被重定向到了 explore 页面")
            print("可能的原因:")
            print("1. 需要登录才能搜索")
            print("2. 反爬虫机制")
            print("3. 需要设置正确的headers")
            print("4. URL参数不正确")
        else:
            print("✓ 成功访问搜索结果页")
        
    except Exception as e:
        print(f"出错: {e}")
        import traceback
        traceback.print_exc()
