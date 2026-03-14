#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书搜索结果爬取脚本 - 最终版
处理Cookie授权，智能等待内容加载，提取图文
"""

import os
import json
import time
import random
from urllib.parse import urljoin, quote
from playwright.sync_api import sync_playwright, TimeoutError

class XiaohongshuFinalCrawler:
    """小红书最终爬虫"""
    
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
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--start-maximized'
                ]
            )
            
            context = browser.new_context(
                user_agent=self.user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN'
            )
            
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """)
            
            page = context.new_page()
            
            try:
                search_url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web_explore_feed"
                print(f"\n访问搜索页面: {search_url}")
                
                page.goto(search_url, timeout=60000, wait_until='domcontentloaded')
                time.sleep(3)
                
                print(f"页面标题: {page.title()}")
                
                # 处理Cookie授权弹窗
                self._handle_cookie_consent(page)
                
                # 保存处理Cookie后的页面
                self._save_html(page, 'after_cookie.html')
                
                # 等待搜索结果加载
                self._wait_for_content(page)
                
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
    
    def _handle_cookie_consent(self, page):
        """处理Cookie授权弹窗"""
        print("处理Cookie授权弹窗...")
        try:
            # 尝试点击"接受"按钮
            accept_selectors = [
                'button:has-text("接受")',
                'button:has-text("同意")',
                '.cookie-banner__btn',
                '[data-testid="cookie-accept"]'
            ]
            
            for selector in accept_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=2000):
                        btn.click(timeout=2000)
                        print("点击了接受按钮")
                        time.sleep(2)
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"处理Cookie弹窗时出错: {e}")
    
    def _wait_for_content(self, page, timeout=15):
        """等待页面内容加载"""
        print("等待内容加载...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 检查是否有文章链接
            links = page.locator('a').all()
            for link in links:
                try:
                    href = link.get_attribute('href', timeout=500)
                    if href and ('/note/' in href or '/item/' in href):
                        print("检测到文章链接")
                        return
                except:
                    continue
            
            # 尝试滚动
            page.evaluate('window.scrollTo(0, 100)')
            time.sleep(1)
        
        print("等待超时，继续执行")
    
    def _extract_article_urls(self, page):
        """从页面提取文章链接"""
        urls = []
        
        # 方法1: 查找所有a标签
        links = page.locator('a').all()
        print(f"页面共有 {len(links)} 个链接")
        
        for link in links:
            try:
                href = link.get_attribute('href', timeout=500)
                if href:
                    # 匹配小红书笔记URL模式
                    if '/note/' in href or '/item/' in href:
                        full_url = urljoin('https://www.xiaohongshu.com', href)
                        clean_url = full_url.split('?')[0]
                        if clean_url not in urls and 'xiaohongshu.com' in clean_url:
                            urls.append(clean_url)
            except:
                continue
        
        # 方法2: 从页面HTML中提取
        if not urls:
            try:
                html = page.content()
                import re
                pattern = r'https?://(?:www\.)?xiaohongshu\.com/(?:note|item)/\d+'
                found = re.findall(pattern, html)
                for url in found:
                    if url not in urls:
                        urls.append(url)
            except:
                pass
        
        # 方法3: 查找包含note-id的元素
        if not urls:
            try:
                elements = page.locator('[data-note-id]').all()
                print(f"找到 {len(elements)} 个带data-note-id的元素")
                for elem in elements:
                    note_id = elem.get_attribute('data-note-id', timeout=500)
                    if note_id:
                        url = f'https://www.xiaohongshu.com/note/{note_id}'
                        if url not in urls:
                            urls.append(url)
            except:
                pass
        
        return urls
    
    def _crawl_article(self, context, url):
        """爬取单篇文章"""
        page = context.new_page()
        
        try:
            page.goto(url, timeout=60000, wait_until='domcontentloaded')
            time.sleep(3)
            
            # 处理可能的Cookie弹窗
            self._handle_cookie_consent(page)
            
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
        selectors = [
            'meta[property="og:title"]::attr(content)',
            'meta[name="title"]::attr(content)',
            'h1::text',
            '.title::text',
            '.note-title::text'
        ]
        
        for selector in selectors:
            try:
                if '::attr' in selector:
                    elem = page.locator(selector.split('::')[0]).first
                    title = elem.get_attribute(selector.split('(')[1].split(')')[0], timeout=1000)
                else:
                    title = page.locator(selector).first.text_content(timeout=1000)
                if title and title.strip():
                    return title.strip()
            except:
                continue
        
        try:
            return page.title()
        except:
            return "无标题"
    
    def _get_content(self, page):
        """提取内容"""
        content = []
        
        # 从meta标签获取
        try:
            desc = page.locator('meta[property="og:description"]').first.get_attribute('content', timeout=1000)
            if desc and desc.strip():
                content.append(desc.strip())
        except:
            pass
        
        # 提取主要内容
        selectors = [
            '.desc ::text',
            '.content ::text',
            '.note-content ::text',
            '.detail ::text',
            'div[class*="content"] ::text',
            'div[class*="desc"] ::text'
        ]
        
        for selector in selectors:
            try:
                texts = page.locator(selector).all_text_contents()
                for text in texts:
                    text = text.strip()
                    if text and len(text) > 5:
                        content.append(text)
            except:
                continue
        
        # 去重并合并
        unique_content = list(dict.fromkeys(content))
        return '\n'.join(unique_content) if unique_content else "无内容"
    
    def _get_images(self, page):
        """提取图片"""
        images = []
        
        # 从meta标签获取
        try:
            img = page.locator('meta[property="og:image"]').first.get_attribute('content', timeout=1000)
            if img:
                images.append(img)
        except:
            pass
        
        # 从页面提取图片
        try:
            imgs = page.locator('img').all()
            for img in imgs[:20]:  # 限制数量
                try:
                    src = img.get_attribute('src', timeout=500) or img.get_attribute('data-src', timeout=500)
                    if src and src.startswith('http'):
                        if any(key in src for key in ['xhsimage', 'xiaohongshu', 'xhscdn', 'qpic']):
                            if src not in images:
                                images.append(src)
                except:
                    continue
        except:
            pass
        
        return images
    
    def _get_author(self, page):
        """提取作者"""
        selectors = [
            'meta[name="author"]::attr(content)',
            '.author ::text',
            '.username ::text',
            '.nickname ::text'
        ]
        
        for selector in selectors:
            try:
                if '::attr' in selector:
                    elem = page.locator(selector.split('::')[0]).first
                    author = elem.get_attribute(selector.split('(')[1].split(')')[0], timeout=1000)
                else:
                    author = page.locator(selector).first.text_content(timeout=1000)
                if author and author.strip():
                    return author.strip()
            except:
                continue
        
        return "未知作者"
    
    def _save_html(self, page, filename):
        """保存HTML用于调试"""
        try:
            html_path = os.path.join(self.base_dir, filename)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(page.content())
        except:
            pass
    
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
    print("小红书最终爬取工具")
    print("=" * 60)
    
    try:
        crawler = XiaohongshuFinalCrawler(headless=HEADLESS)
        results = crawler.crawl(KEYWORD, MAX_ARTICLES)
        
        if results:
            print("\n爬取结果:")
            for i, r in enumerate(results, 1):
                print(f"\n{i}. 标题: {r['title']}")
                print(f"   作者: {r['author']}")
                print(f"   图片数: {len(r['images'])}")
                if r['content']:
                    print(f"   内容预览: {r['content'][:60]}...")
                
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()