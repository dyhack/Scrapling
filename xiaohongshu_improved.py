#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书搜索结果爬取脚本 - 改进版
使用更灵活的选择器和页面分析方法
"""

import os
import json
import time
import random
import re
from urllib.parse import urljoin, quote
from scrapling.fetchers import StealthySession, StealthyFetcher

class XiaohongshuCrawler:
    """改进版小红书爬虫"""
    
    def __init__(self, headless=True):
        self.headless = headless
        self.base_dir = "xiaohongshu_data"
        os.makedirs(self.base_dir, exist_ok=True)
        
    def crawl(self, keyword, max_articles=5):
        """主爬取函数"""
        encoded_keyword = quote(keyword)
        results = []
        
        print(f"开始爬取小红书关键词: {keyword}")
        print(f"输出目录: {self.base_dir}")
        
        with StealthySession(
            headless=self.headless,
            solve_cloudflare=True,
            network_idle=True,
            timeout=60
        ) as session:
            # 访问搜索页面
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web_explore_feed"
            print(f"\n访问搜索页面: {search_url}")
            
            page = session.fetch(search_url, google_search=True)
            print(f"页面状态码: {page.status}")
            
            # 等待页面加载
            time.sleep(5)
            
            # 保存页面HTML用于调试
            self._save_html(page, 'search_page.html')
            
            # 提取文章链接（多种方法）
            article_urls = self._extract_article_urls(page)
            print(f"找到 {len(article_urls)} 篇文章链接")
            
            # 爬取每篇文章
            for i, url in enumerate(article_urls[:max_articles], 1):
                print(f"\n[{i}/{min(max_articles, len(article_urls))}] 爬取: {url}")
                try:
                    article = self._crawl_article(session, url)
                    if article:
                        results.append(article)
                        self._save_article(article)
                    time.sleep(random.uniform(3, 6))
                except Exception as e:
                    print(f"   失败: {str(e)[:60]}")
                    continue
        
        print(f"\n{'='*60}")
        print(f"爬取完成！成功获取 {len(results)} 篇文章")
        print('='*60)
        
        # 保存汇总
        self._save_summary(results, keyword)
        return results
    
    def _extract_article_urls(self, page):
        """从页面提取文章链接 - 使用多种方法"""
        urls = []
        
        # 方法1: 查找所有a标签中包含note的链接
        try:
            all_links = page.css('a')
            print(f"页面共有 {len(all_links)} 个链接")
            
            for link in all_links:
                href = link.attrib.get('href', '')
                if href:
                    # 匹配小红书笔记URL模式
                    if re.search(r'/note/\d+', href) or re.search(r'xiaohongshu.com/note/', href):
                        full_url = urljoin('https://www.xiaohongshu.com', href)
                        clean_url = full_url.split('?')[0]
                        if clean_url not in urls and 'xiaohongshu.com' in clean_url:
                            urls.append(clean_url)
        except Exception as e:
            print(f"方法1失败: {e}")
        
        # 方法2: 从页面文本中提取URL
        if not urls:
            try:
                html_content = str(page)
                url_pattern = r'https?://(?:www\.)?xiaohongshu\.com/note/\d+'
                found_urls = re.findall(url_pattern, html_content)
                for url in found_urls:
                    if url not in urls:
                        urls.append(url)
            except Exception as e:
                print(f"方法2失败: {e}")
        
        # 方法3: 查找笔记卡片元素
        if not urls:
            try:
                # 查找可能包含笔记的元素
                note_cards = page.css('[data-id]') or page.css('[data-note-id]')
                print(f"找到 {len(note_cards)} 个可能的笔记卡片")
            except:
                pass
        
        return list(dict.fromkeys(urls))  # 去重
    
    def _crawl_article(self, session, url):
        """爬取单篇文章"""
        page = session.fetch(url, google_search=False)
        if page.status != 200:
            return None
        
        time.sleep(3)
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
    
    def _get_title(self, page):
        """提取标题"""
        # 从meta标签获取
        try:
            title = page.css('meta[property="og:title"]::attr(content)').get()
            if title:
                return title.strip()
        except:
            pass
        
        # 从title标签获取
        try:
            title = page.css('title::text').get()
            if title:
                return title.strip()
        except:
            pass
        
        return "无标题"
    
    def _get_content(self, page):
        """提取内容"""
        content = []
        
        # 从meta描述获取
        try:
            desc = page.css('meta[property="og:description"]::attr(content)').get()
            if desc:
                content.append(desc.strip())
        except:
            pass
        
        # 提取所有可见文本
        try:
            texts = page.css('div::text, p::text, span::text').getall()
            for text in texts:
                text = text.strip()
                if text and len(text) > 10:  # 过滤短文本
                    content.append(text)
        except:
            pass
        
        return '\n'.join(content) if content else "无内容"
    
    def _get_images(self, page):
        """提取图片"""
        images = []
        
        # 从meta标签获取
        try:
            img = page.css('meta[property="og:image"]::attr(content)').get()
            if img:
                images.append(img)
        except:
            pass
        
        # 从页面获取图片
        try:
            imgs = page.css('img')
            for img in imgs:
                src = img.attrib.get('src', '') or img.attrib.get('data-src', '')
                if src and src.startswith('http'):
                    if 'xhsimage' in src or 'xiaohongshu' in src:
                        if src not in images:
                            images.append(src)
        except:
            pass
        
        return images
    
    def _get_author(self, page):
        """提取作者"""
        try:
            author = page.css('meta[name="author"]::attr(content)').get()
            if author:
                return author.strip()
        except:
            pass
        return "未知作者"
    
    def _save_html(self, page, filename):
        """保存HTML用于调试"""
        html_path = os.path.join(self.base_dir, filename)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(str(page))
    
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
    print("小红书爬取工具 - 改进版")
    print("=" * 60)
    
    try:
        crawler = XiaohongshuCrawler(headless=HEADLESS)
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
