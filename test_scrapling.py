#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Scrapling基本功能
"""

from scrapling.fetchers import StealthyFetcher, StealthySession

def test_basic_fetch():
    """测试基本的页面获取功能"""
    print("测试1: 使用StealthyFetcher获取页面")
    try:
        page = StealthyFetcher.fetch('https://quotes.toscrape.com/', headless=True)
        print(f"状态码: {page.status}")
        quotes = page.css('.quote .text::text').getall()
        print(f"获取到 {len(quotes)} 条名言")
        if quotes:
            print(f"第一条名言: {quotes[0][:50]}...")
        print("测试1成功！")
    except Exception as e:
        print(f"测试1失败: {e}")

def test_session():
    """测试StealthySession"""
    print("\n测试2: 使用StealthySession")
    try:
        with StealthySession(headless=True) as session:
            page = session.fetch('https://quotes.toscrape.com/page/1/')
            print(f"状态码: {page.status}")
            quotes = page.css('.quote .text::text').getall()
            print(f"第一页获取到 {len(quotes)} 条名言")
        print("测试2成功！")
    except Exception as e:
        print(f"测试2失败: {e}")

def test_xiaohongshu_access():
    """测试访问小红书页面"""
    print("\n测试3: 尝试访问小红书页面")
    try:
        page = StealthyFetcher.fetch('https://www.xiaohongshu.com/', headless=True, solve_cloudflare=True, timeout=30)
        print(f"状态码: {page.status}")
        print(f"页面标题: {page.css('title::text').get() or '未获取到标题'}")
        print("测试3成功！")
    except Exception as e:
        print(f"测试3失败: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Scrapling功能测试")
    print("=" * 50)
    
    test_basic_fetch()
    test_session()
    test_xiaohongshu_access()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
