#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本：深入分析小红书页面结构
"""

from scrapling.fetchers import StealthySession
from playwright.sync_api import Page as PlaywrightPage
import time

def debug_page_structure():
    """深入分析小红书页面结构"""
    with StealthySession(
        headless=False,
        solve_cloudflare=False,
        network_idle=False,
        timeout=30000
    ) as session:
        url = "https://www.xiaohongshu.com/search_result?keyword=%E4%B8%80%E5%8A%A0turbo6&source=web_explore_feed"
        print(f"访问: {url}")
        
        def page_action(page: PlaywrightPage):
            print("执行页面操作...")
            
            page.set_default_timeout(10000)
            
            try:
                page.wait_for_load_state('domcontentloaded', timeout=10000)
                print("DOM加载完成")
            except Exception as e:
                print(f"DOM加载超时: {e}")
            
            time.sleep(5)
            
            # 处理cookie
            try:
                agree_btn = page.locator('button:has-text("同意")').first
                if agree_btn.is_visible(timeout=2000):
                    agree_btn.click(timeout=1000)
                    print("点击了同意按钮")
                    time.sleep(2)
            except Exception:
                pass
            
            # 等待内容加载
            time.sleep(3)
            
            # 打印页面标题
            print(f"\n页面标题: {page.title()}")
            
            # 分析页面中的主要元素
            print("\n" + "="*60)
            print("分析主要页面元素")
            print("="*60)
            
            # 查找所有可能的内容容器
            selectors = [
                ('div[class*="note"]', '包含note的div'),
                ('div[class*="card"]', '包含card的div'),
                ('div[class*="item"]', '包含item的div'),
                ('div[class*="feed"]', '包含feed的div'),
                ('div[class*="result"]', '包含result的div'),
                ('section', 'section标签'),
                ('main', 'main标签'),
                ('article', 'article标签'),
            ]
            
            for selector, desc in selectors:
                try:
                    count = page.locator(selector).count()
                    if count > 0:
                        print(f"{desc}: {count} 个元素")
                except Exception:
                    pass
            
            # 查找所有有数据属性的元素
            print("\n" + "="*60)
            print("查找带data-*属性的元素")
            print("="*60)
            try:
                elements_with_data = page.evaluate("""() => {
                    const all = document.querySelectorAll('*');
                    const result = [];
                    for (let el of all) {
                        if (el.hasAttributes()) {
                            for (let attr of el.attributes) {
                                if (attr.name.startsWith('data-')) {
                                    result.push({
                                        tag: el.tagName,
                                        attr: attr.name,
                                        value: attr.value
                                    });
                                    break;
                                }
                            }
                        }
                    }
                    return result;
                }""")
                
                data_types = {}
                for item in elements_with_data:
                    key = item['attr']
                    data_types[key] = data_types.get(key, 0) + 1
                
                for attr_name, count in data_types.items():
                    print(f"  {attr_name}: {count} 个元素")
            except Exception as e:
                print(f"分析data属性失败: {e}")
            
            # 分析网络请求
            print("\n" + "="*60)
            print("分析网络请求")
            print("="*60)
            try:
                requests = page.evaluate("""() => {
                    return performance.getEntriesByType('resource')
                        .filter(e => e.initiatorType === 'fetch' || e.initiatorType === 'xmlhttprequest')
                        .map(e => ({name: e.name, type: e.initiatorType}));
                }""")
                
                print(f"发现 {len(requests)} 个API请求")
                for req in requests[:10]:
                    if 'xiaohongshu' in req['name']:
                        print(f"  - {req['name'][:100]}...")
            except Exception as e:
                print(f"分析请求失败: {e}")
            
            # 保存完整页面内容用于分析
            print("\n" + "="*60)
            print("保存页面内容")
            print("="*60)
            try:
                content = page.content()
                with open("full_page.html", "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"页面内容已保存到 full_page.html (长度: {len(content)})")
            except Exception as e:
                print(f"保存页面失败: {e}")
        
        session.fetch(url, page_action=page_action, wait=2000)

if __name__ == "__main__":
    debug_page_structure()
