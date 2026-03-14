#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书搜索结果爬取脚本 - 动态渲染版
使用Playwright直接操作浏览器，处理JavaScript动态渲染
"""

import os
import json
import time
import random
from urllib.parse import urljoin, quote
from playwright.sync_api import sync_playwright, Browser, Page

class XiaohongshuDynamicCrawler:
    """小红书动态爬虫"""
    
    def __init__(self, headless=False):
        self.headless = headless
        self.base_dir = "xiaohongshu_data"
        os.makedirs(self.base_dir, exist_ok=True)
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        
    def crawl(self, keyword, max_articles=5):
        """主爬取函数"""
        encoded_keyword = quote(keyword)
        results = []
        
        print(f"开始爬取小红书关键词: {keyword}")
        print(f"输出目录: {self.base_dir}")
        
        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--start-maximized'
                ]
            )
            
            # 创建上下文
            context = browser.new_context(
                user_agent=self.user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN'
            )
            
            # 隐藏webdriver特征
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """)
            
            page = context.new_page()
            
            try:
                # 访问搜索页面
                search_url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web_explore_feed"
                print(f"\n访问搜索页面: {search_url}")
                
                page.goto(search_url, timeout=60000, wait_until='domcontentloaded')
                time.sleep(5)
                
                # 保存页面HTML
                self._save_html(page, 'search_page.html')
                print(f"页面标题: {page.title()}")
                
                # 滚动页面加载更多内容
                self._scroll_page(page)
                
                # 提取文章链接
                article_urls = self._extract_article_urls(page)
                print(f"找到 {len(article_urls)} 篇文章链接")
                
                # 爬取每篇文章
                for i, url in enumerate(article_urls[:max_articles], 1):
                    print(f"\n[{i}/{min(max_articles, len(article_urls))}] 爬取: {url}")
                    try:
                        article = self._crawl_article(context, url)
                        if article:
                            results.append(article)
                            self._save_article(article)
                        time.sleep(random.uniform(2, 4))
                    except Exception as e:
                        print(f"   失败: {str(e)[:80]}")
                        continue
                
            finally:
                browser.close()
        
        print(f"\n{'='*60}")
        print(f"爬取完成！成功获取 {len(results)} 篇文章")
        print('='*60)
        
        self._save_summary(results, keyword)
        return results
    
    def _scroll_page(self, page, scroll_times=2):
        """滚动页面加载更多内容"""
        print("滚动页面加载内容...")
        for i in range(scroll_times):
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(3)
    
    def _extract_article_urls(self, page):
        """从页面提取文章链接"""
        urls = []
        
        # 查找所有笔记卡片链接
        links = page.locator('a').all()
        print(f"页面共有 {len(links)} 个链接")
        
        for link in links:
            try:
                href = link.get_attribute('href', timeout=1000)
                if href and ('/note/' in href or '/item/' in href):
                    full_url = urljoin('https://www.xiaohongshu.com', href)
                    clean_url = full_url.split('?')[0]
                    if clean_url not in urls:
                        urls.append(clean_url)
            except:
                continue
        
        # 如果没找到，尝试其他选择器
        if not urls:
            try:
                # 查找包含note的元素
                elements = page.locator('[data-note-id]').all()
                print(f"找到 {len(elements)} 个带data-note-id的元素")
            except:
                pass
        
        return urls
    
    def _crawl_article(self, context, url):
        """爬取单篇文章"""
        page = context.new_page()
        
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state('networkidle', timeout=30000)
            time.sleep(2)
            
            # 保存HTML
            self._save_html(page, f'article_{url.split("/")[-1]}.html')
            
            # 提取元数据
            title = self._get_title(page)
            content = self._get_content(page)
            images = self._get_images(page)
            author = self._get_author(page)
            
            return {
                'url': url,
                'title': title,
                'content': content,
                'author': author,
                'images': images,
                'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        finally:
            page.close()
    
    def _get_title(self, page):
        """提取标题"""
        try:
            # 尝试meta标签
            title = page.locator('meta[property="og:title"]').get_attribute('content', timeout=2000)
            if title:
                return title.strip()
        except:
            pass
        
        try:
            return page.title()
        except:
            return "无标题"
    
    def _get_content(self, page):
        """提取内容"""
        content = []
        
        try:
            desc = page.locator('meta[property="og:description"]').get_attribute('content', timeout=2000)
            if desc:
                content.append(desc.strip())
        except:
            pass
        
        # 提取可见文本
        try:
            elements = page.locator('div, p, span').all()
            for elem in elements[:50]:
                try:
                    text = elem.text_content(timeout=500)
                    if text and len(text.strip()) > 10:
                        content.append(text.strip())
                except:
                    continue
        except:
            pass
        
        return '\n'.join(content) if content else "无内容"
    
    def _get_images(self, page):
        """提取图片"""
        images = []
        
        try:
            img = page.locator('meta[property="og:image"]').get_attribute('content', timeout=2000)
            if img:
                images.append(img)
        except:
            pass
        
        try:
            imgs = page.locator('img').all()
            for img in imgs:
                try:
                    src = img.get_attribute('src', timeout=500) or img.get_attribute('data-src', timeout=500)
                    if src and src.startswith('http'):
                        if 'xhsimage' in src or 'xiaohongshu' in src or 'xhscdn' in src:
                            if src not in images:
                                images.append(src)
                except:
                    continue
        except:
            pass
        
        return images
    
    def _get_author(self, page):
        """提取作者"""
        try:
            author = page.locator('meta[name="author"]').get_attribute('content', timeout=2000)
            if author:
                return author.strip()
        except:
            pass
        return "未知作者"
    
    def _save_html(self, page, filename):
        """保存HTML"""
        html_path = os.path.join(self.base_dir, filename)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(page.content())
    
    def _save_article(self, article):
        """保存文章"""
        article_id = article['url'].split('/')[-1]
        path = os.path.join(self.base_dir, f'article_{article_id}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(article, f, ensure_ascii=False, indent=2)
        print(f"   已保存: {path}")
    
    def _save_summary(self, results, keyword):
        """保存汇总"""
        summary = {
            'keyword': keyword,
            'total': len(results),
            'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'articles': results
        }
        path = os.path.join(self.base_dir, f'summary_{int(time.time())}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

def main():
    KEYWORD = "一加turbo6"
    MAX_ARTICLES = 5
    HEADLESS = False  # 设为False可以看到浏览器
    
    print("=" * 60)
    print("小红书动态爬取工具")
    print("=" * 60)
    
    try:
        crawler = XiaohongshuDynamicCrawler(headless=HEADLESS)
        results = crawler.crawl(KEYWORD, MAX_ARTICLES)
        
        if results:
            print("\n爬取结果:")
            for i, r in enumerate(results, 1):
                print(f"\n{i}. 标题: {r['title']}")
                print(f"   作者: {r['author']}")
                print(f"   图片数: {len(r['images'])}")
                
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()