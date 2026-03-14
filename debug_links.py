#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本：分析小红书页面链接提取
"""

from scrapling.fetchers import StealthySession
from playwright.sync_api import Page as PlaywrightPage
import time

def debug_xiaohongshu_links():
    """调试小红书链接提取"""
    with StealthySession(
        headless=False,
        solve_cloudflare=False,
        network_idle=False,
        timeout=30000
    ) as session:
        url = "https://www.xiaohongshu.com/search_result?keyword=%E4%B8%80%E5%8A%A0turbo6&source=web_explore_feed"
        print(f"访问: {url}")
        
        extracted_urls = set()
        
        def page_action(page: PlaywrightPage):
            print("执行页面操作...")
            
            page.set_default_timeout(10000)
            
            try:
                page.wait_for_load_state('domcontentloaded', timeout=10000)
                print("DOM加载完成")
            except Exception as e:
                print(f"DOM加载超时: {e}")
            
            time.sleep(3)
            
            # 处理cookie
            try:
                agree_btn = page.locator('button:has-text("同意")').first
                if agree_btn.is_visible(timeout=2000):
                    agree_btn.click(timeout=1000)
                    print("点击了同意按钮")
                    time.sleep(1)
            except Exception:
                pass
            
            # 滚动页面
            for i in range(3):
                print(f"滚动第 {i+1} 次")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            
            # 方法1: 通过JavaScript获取所有链接
            print("\n" + "="*60)
            print("方法1: JavaScript提取所有链接")
            print("="*60)
            try:
                all_links = page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('a')).map(a => ({
                        href: a.href,
                        text: a.textContent || '',
                        outerHTML: a.outerHTML.substring(0, 200)
                    }));
                }""")
                
                print(f"找到 {len(all_links)} 个链接")
                note_links = [link for link in all_links if 'note' in link['href'].lower()]
                print(f"包含'note'的链接: {len(note_links)} 个")
                
                for link in note_links[:10]:
                    print(f"  - {link['href']}")
                    extracted_urls.add(link['href'])
            except Exception as e:
                print(f"JavaScript提取失败: {e}")
            
            # 方法2: 搜索页面中的所有note链接
            print("\n" + "="*60)
            print("方法2: 正则表达式搜索note链接")
            print("="*60)
            try:
                page_content = page.content()
                import re
                note_pattern = r'https://www\.xiaohongshu\.com/note/[a-zA-Z0-9]+'
                matches = re.findall(note_pattern, page_content)
                unique_matches = list(set(matches))
                print(f"找到 {len(unique_matches)} 个唯一note链接")
                for match in unique_matches[:10]:
                    print(f"  - {match}")
                    extracted_urls.add(match)
            except Exception as e:
                print(f"正则搜索失败: {e}")
            
            # 方法3: 通过元素选择器查找
            print("\n" + "="*60)
            print("方法3: 查找可能包含链接的元素")
            print("="*60)
            try:
                items = page.locator('[data-testid*="note"]').all()
                print(f"找到 {len(items)} 个包含note的元素")
                for item in items[:5]:
                    try:
                        href = item.get_attribute('href')
                        if href:
                            print(f"  - {href}")
                    except Exception:
                        pass
            except Exception as e:
                print(f"元素查找失败: {e}")
        
        session.fetch(url, page_action=page_action, wait=2000)
        
        print("\n" + "="*60)
        print("最终提取的所有链接:")
        print("="*60)
        for url in extracted_urls:
            print(f"  - {url}")
        print(f"\n总计: {len(extracted_urls)} 个链接")

if __name__ == "__main__":
    debug_xiaohongshu_links()
