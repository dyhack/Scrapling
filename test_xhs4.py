#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试小红书页面数据加载 - 深度分析
"""
import time
import json
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
    page.wait_for_timeout(8000)
    
    # 检查是否有cookie提示框
    try:
        cookie_accept = page.locator("button:has-text('同意'), button:has-text('接受'), button:has-text('Accept')")
        if cookie_accept.count() > 0:
            print("发现cookie提示，点击同意...")
            cookie_accept.first.click()
            page.wait_for_timeout(2000)
    except:
        pass
    
    # 检查是否有登录提示
    try:
        login_close = page.locator("div[class*='close'], svg[class*='close'], button[aria-label='关闭']")
        if login_close.count() > 0:
            print("尝试关闭登录弹窗...")
            login_close.first.click(timeout=2000)
    except:
        pass
    
    # 滚动页面触发加载
    print("滚动页面触发内容加载...")
    for i in range(2):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(2000)
    
    # 等待笔记元素出现
    try:
        page.wait_for_selector(".note-item", timeout=10000)
        print("找到.note-item元素")
    except Exception as e:
        print(f"等待.note-item超时: {e}")
    
    # 查找所有包含data-id的元素
    data_ids = page.evaluate("""() => {
        const elements = document.querySelectorAll('[data-id]');
        const ids = [];
        elements.forEach(el => {
            const id = el.getAttribute('data-id');
            if (id && id.length > 10) ids.push(id);
        });
        return ids.slice(0, 20);
    }""")
    print(f"找到data-id元素: {data_ids}")
    
    # 检查window.__INITIAL_STATE__
    init_state = page.evaluate("() => window.__INITIAL_STATE__ || null")
    if init_state:
        print("window.__INITIAL_STATE__ 存在")
        # 搜索相关数据
        if 'search' in init_state:
            print(f"search对象键: {list(init_state['search'].keys())}")
            if 'feeds' in init_state['search']:
                print(f"search.feeds数量: {len(init_state['search']['feeds'])}")
            if 'searchFeedsWrapper' in init_state['search']:
                print(f"searchFeedsWrapper存在: {init_state['search']['searchFeedsWrapper'] is not None}")
    
    # 检查网络请求
    print("检查网络请求...")
    requests = page.evaluate("""() => {
        const requests = [];
        const origOpen = XMLHttpRequest.prototype.open;
        const origSend = XMLHttpRequest.prototype.send;
        XMLHttpRequest.prototype.open = function(method, url) {
            this._url = url;
            this._method = method;
            return origOpen.apply(this, arguments);
        };
        XMLHttpRequest.prototype.send = function(body) {
            if (this._url.includes('xiaohongshu') || this._url.includes('/api/') || this._url.includes('/sns/')) {
                requests.push({url: this._url, method: this._method});
            }
            return origSend.apply(this, arguments);
        };
        return requests.slice(0, 20);
    }""")
    print(f"捕获的API请求: {requests}")
    
    # 查找笔记链接 - 使用不同的选择器
    print("查找笔记链接...")
    
    # 方法1: 查找所有a标签的href
    all_links = page.evaluate("""() => {
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            const href = a.getAttribute('href');
            if (href) links.push(href);
        });
        return links;
    }""")
    
    note_links = [l for l in all_links if '/note/' in str(l)]
    item_links = [l for l in all_links if '/item/' in str(l)]
    
    print(f"找到/note/链接: {note_links[:10]}")
    print(f"找到/item/链接: {item_links[:10]}")
    
    # 方法2: 查找包含xsec_token的链接
    xsec_links = [l for l in all_links if 'xsec_token' in str(l)]
    print(f"包含xsec_token的链接数: {len(xsec_links)}")
    print(f"前10个xsec链接: {xsec_links[:10]}")
    
    # 检查note-item内部结构
    note_items_html = page.evaluate("""() => {
        const items = document.querySelectorAll('.note-item');
        const htmls = [];
        items.forEach((item, i) => {
            if (i < 5) {
                htmls.push(item.outerHTML.substring(0, 2000));
            }
        });
        return htmls;
    }""")
    
    for i, html in enumerate(note_items_html):
        print(f"\n=== note-item {i} 预览 ===")
        print(html[:500])
    
    # 查找包含链接的元素
    links_in_notes = page.evaluate("""() => {
        const items = document.querySelectorAll('.note-item');
        const links = [];
        items.forEach(item => {
            item.querySelectorAll('a').forEach(a => {
                const href = a.getAttribute('href');
                if (href) links.push(href);
            });
        });
        return links;
    }""")
    print(f"\n.note-item中的链接: {links_in_notes[:20]}")
    
    # 获取完整HTML
    html = page.content()
    page_data["html"] = html
    page_data["title"] = page.title()
    page_data["note_links"] = note_links
    page_data["item_links"] = item_links
    page_data["xsec_links"] = xsec_links
    page_data["all_links_count"] = len(all_links)
    
    print(f"\npage_action 完成")
    print(f"页面标题: {page_data['title']}")
    print(f"总链接数: {len(all_links)}")
    print(f"note链接数: {len(note_links)}")
    print(f"item链接数: {len(item_links)}")

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
        
        print(f"\n状态码: {page.status}")
        print(f"HTML长度: {len(page_data.get('html', ''))}")
        
        # 用Scrapling的选择器查找
        print("\n=== 使用Scrapling选择器查找 ===")
        
        # 查找所有包含note-item的元素
        note_items = page.css(".note-item")
        print(f".note-item 元素数量: {len(note_items)}")
        
        for i, item in enumerate(note_items[:5]):
            # 查找a标签
            links = item.css("a")
            print(f"\n笔记 {i} 的链接数: {len(links)}")
            for link in links:
                href = link.attr("href")
                if href:
                    print(f"  - {href}")
            
            # 查找图片
            imgs = item.css("img")
            print(f"笔记 {i} 的图片数: {len(imgs)}")
            for img in imgs:
                src = img.attr("src")
                if src:
                    print(f"  - img: {src[:100]}")
        
        # 查找所有可能的笔记链接
        print("\n=== 查找所有可能的笔记链接 ===")
        all_links = page.css("a")
        print(f"页面总链接数: {len(all_links)}")
        
        note_urls = []
        for link in all_links:
            href = link.attr("href")
            if href and ("/note/" in href or "/item/" in href):
                note_urls.append(href)
        
        print(f"找到笔记链接: {note_urls}")
        
        # 保存页面
        with open("xhs_page4.html", "w", encoding="utf-8") as f:
            f.write(page_data.get("html", ""))
        print("\n页面已保存到 xhs_page4.html")
        
    except Exception as e:
        print(f"出错: {e}")
        import traceback
        traceback.print_exc()
