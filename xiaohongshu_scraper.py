#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书搜索页面爬取脚本
功能：爬取小红书搜索结果页面的文章图文内容
"""

import os
import json
import time
from urllib.parse import urljoin, urlparse
from scrapling.fetchers import StealthyFetcher, StealthySession

class XiaohongshuScraper:
    """小红书爬虫类"""
    
    def __init__(self, headless=True):
        """
        初始化爬虫
        :param headless: 是否使用无头浏览器模式，默认为True
        """
        self.headless = headless
        # 创建存储目录
        self.output_dir = "xiaohongshu_output"
        self.images_dir = os.path.join(self.output_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
        
    def search_and_scrape(self, keyword, max_articles=10):
        """
        搜索关键词并爬取结果
        :param keyword: 搜索关键词
        :param max_articles: 最大爬取文章数量
        :return: 爬取结果列表
        """
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_explore_feed"
        print(f"正在访问搜索页面: {search_url}")
        
        # 使用StealthySession保持会话
        with StealthySession(headless=self.headless, solve_cloudflare=True) as session:
            # 访问搜索页面
            page = session.fetch(search_url, google_search=False)
            print(f"页面状态码: {page.status}")
            
            # 等待页面加载完成
            time.sleep(3)
            
            # 提取文章链接
            article_links = self._extract_article_links(page)
            print(f"找到 {len(article_links)} 篇文章链接")
            
            results = []
            # 爬取每篇文章
            for i, link in enumerate(article_links[:max_articles], 1):
                print(f"\n正在爬取第 {i}/{min(max_articles, len(article_links))} 篇文章: {link}")
                try:
                    article_data = self._scrape_article(session, link)
                    if article_data:
                        results.append(article_data)
                        self._save_article(article_data)
                    time.sleep(2)  # 避免请求过于频繁
                except Exception as e:
                    print(f"爬取文章失败: {e}")
                    continue
        
        print(f"\n爬取完成！共成功爬取 {len(results)} 篇文章")
        return results
    
    def _extract_article_links(self, page):
        """
        从搜索结果页面提取文章链接
        :param page: Scrapling的Selector对象
        :return: 文章链接列表
        """
        article_links = []
        
        # 尝试不同的选择器来提取文章链接
        # 方法1: 通过笔记卡片的a标签
        note_cards = page.css('a[href*="/note/"]')
        for card in note_cards:
            href = card.attrib.get('href', '')
            if href and '/note/' in href:
                full_url = urljoin('https://www.xiaohongshu.com', href)
                if full_url not in article_links:
                    article_links.append(full_url)
        
        # 如果没找到，尝试其他选择器
        if not article_links:
            # 方法2: 通过包含note的链接
            all_links = page.css('a')
            for link in all_links:
                href = link.attrib.get('href', '')
                if href and '/note/' in href and 'https' in href:
                    if href not in article_links:
                        article_links.append(href)
        
        return article_links
    
    def _scrape_article(self, session, url):
        """
        爬取单篇文章
        :param session: StealthySession对象
        :param url: 文章URL
        :return: 文章数据字典
        """
        page = session.fetch(url, google_search=False)
        if page.status != 200:
            print(f"请求失败，状态码: {page.status}")
            return None
        
        time.sleep(2)  # 等待页面完全加载
        
        # 提取文章标题
        title = self._extract_title(page)
        
        # 提取文章内容
        content = self._extract_content(page)
        
        # 提取图片
        images = self._extract_images(page, url)
        
        # 提取作者信息
        author = self._extract_author(page)
        
        # 提取发布时间
        publish_time = self._extract_publish_time(page)
        
        return {
            'url': url,
            'title': title,
            'content': content,
            'author': author,
            'publish_time': publish_time,
            'images': images,
            'scraped_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _extract_title(self, page):
        """提取文章标题"""
        # 尝试多种选择器
        title_selectors = [
            'h1.title::text',
            'div.title::text',
            'meta[property="og:title"]::attr(content)',
            'meta[name="twitter:title"]::attr(content)'
        ]
        
        for selector in title_selectors:
            try:
                title = page.css(selector).get()
                if title and title.strip():
                    return title.strip()
            except:
                continue
        
        return "无标题"
    
    def _extract_content(self, page):
        """提取文章内容"""
        content_selectors = [
            'div.content::text',
            'div.desc::text',
            'meta[property="og:description"]::attr(content)',
            'meta[name="description"]::attr(content)'
        ]
        
        content_parts = []
        
        # 尝试获取主要内容
        for selector in content_selectors:
            try:
                content = page.css(selector).getall()
                if content:
                    content_parts.extend([c.strip() for c in content if c.strip()])
            except:
                continue
        
        # 如果没找到，尝试获取所有段落文本
        if not content_parts:
            try:
                paragraphs = page.css('p::text').getall()
                content_parts = [p.strip() for p in paragraphs if p.strip()]
            except:
                pass
        
        return '\n'.join(content_parts) if content_parts else "无内容"
    
    def _extract_images(self, page, article_url):
        """提取文章图片"""
        images = []
        
        # 从meta标签获取主图
        try:
            main_image = page.css('meta[property="og:image"]::attr(content)').get()
            if main_image:
                images.append(main_image)
        except:
            pass
        
        # 从页面中提取其他图片
        try:
            img_tags = page.css('img')
            for img in img_tags:
                src = img.attrib.get('src', '')
                if src and src.startswith('http'):
                    # 过滤掉一些小图标和logo
                    if any(keyword in src.lower() for keyword in ['sns-img', 'xiaohongshu', 'note']):
                        if src not in images:
                            images.append(src)
        except:
            pass
        
        return images
    
    def _extract_author(self, page):
        """提取作者信息"""
        author_selectors = [
            'div.author::text',
            'span.username::text',
            'meta[name="author"]::attr(content)'
        ]
        
        for selector in author_selectors:
            try:
                author = page.css(selector).get()
                if author and author.strip():
                    return author.strip()
            except:
                continue
        
        return "未知作者"
    
    def _extract_publish_time(self, page):
        """提取发布时间"""
        time_selectors = [
            'span.time::text',
            'div.date::text',
            'meta[property="article:published_time"]::attr(content)'
        ]
        
        for selector in time_selectors:
            try:
                publish_time = page.css(selector).get()
                if publish_time and publish_time.strip():
                    return publish_time.strip()
            except:
                continue
        
        return "未知时间"
    
    def _save_article(self, article_data):
        """保存文章数据到文件"""
        # 保存为JSON
        json_path = os.path.join(self.output_dir, f"article_{int(time.time())}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)
        
        # 保存为Markdown格式
        md_path = os.path.join(self.output_dir, f"article_{int(time.time())}.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {article_data['title']}\n\n")
            f.write(f"- 作者: {article_data['author']}\n")
            f.write(f"- 发布时间: {article_data['publish_time']}\n")
            f.write(f"- 原文链接: {article_data['url']}\n")
            f.write(f"- 爬取时间: {article_data['scraped_time']}\n\n")
            f.write("## 正文\n\n")
            f.write(f"{article_data['content']}\n\n")
            
            if article_data['images']:
                f.write("## 图片\n\n")
                for i, img_url in enumerate(article_data['images'], 1):
                    f.write(f"![图片{i}]({img_url})\n\n")
        
        print(f"文章已保存到: {json_path}")

def main():
    """主函数"""
    # 搜索关键词（URL编码）
    keyword = "%E4%B8%80%E5%8A%A0turbo6"  # "一加turbo6"的URL编码
    
    # 创建爬虫实例
    # 设置headless=False可以看到浏览器操作过程，便于调试
    scraper = XiaohongshuScraper(headless=False)
    
    print("=" * 60)
    print("小红书爬取工具")
    print("=" * 60)
    print(f"搜索关键词: 一加turbo6")
    print(f"输出目录: {scraper.output_dir}")
    print("=" * 60)
    
    try:
        # 开始爬取，最多爬取10篇文章
        results = scraper.search_and_scrape(keyword, max_articles=10)
        
        # 输出汇总信息
        print("\n" + "=" * 60)
        print("爬取汇总")
        print("=" * 60)
        for i, result in enumerate(results, 1):
            print(f"\n{i}. 标题: {result['title']}")
            print(f"   作者: {result['author']}")
            print(f"   图片数: {len(result['images'])}")
            print(f"   链接: {result['url']}")
        
    except KeyboardInterrupt:
        print("\n用户中断爬取")
    except Exception as e:
        print(f"\n爬取过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
