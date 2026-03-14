#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书高级爬虫
功能：通过多种策略提取小红书搜索结果的文章内容
"""

from typing import List, Set, Dict, Any
from dataclasses import dataclass
from scrapling.fetchers import StealthySession
from playwright.sync_api import Page as PlaywrightPage
import time
import json
import re

@dataclass
class Article:
    """文章数据结构
    用于存储爬取到的小红书文章的完整信息
    """
    title: str           # 文章标题
    content: str         # 文章正文内容
    images: List[str]    # 文章图片URL列表
    author: str          # 作者名称
    url: str             # 文章链接
    publish_time: str    # 发布时间

class XiaohongshuAdvancedCrawler:
    """
    小红书高级爬虫类
    使用多种策略提取文章链接和内容
    """

    def __init__(self, headless: bool = False, timeout: int = 30000):
        """
        初始化爬虫配置
        :param headless: 是否使用无头浏览器模式（默认显示浏览器窗口）
        :param timeout: 页面加载超时时间（毫秒）
        """
        self.headless = headless
        self.timeout = timeout
        self.base_url = "https://www.xiaohongshu.com"
        self._article_urls: Set[str] = set()
        self._article_data: List[Dict[str, Any]] = []

    def _handle_cookie_consent(self, page: PlaywrightPage) -> None:
        """处理小红书的cookie同意弹窗"""
        try:
            agree_selectors = [
                'button:has-text("同意")',
                'button:has-text("同意并继续")',
                'button:has-text("我知道了")',
            ]

            for selector in agree_selectors:
                try:
                    button = page.locator(selector).first
                    if button.is_enabled() and button.is_visible(timeout=1000):
                        button.click(timeout=1000)
                        print("已处理cookie同意弹窗")
                        time.sleep(0.5)
                        break
                except Exception:
                    continue
        except Exception as e:
            print(f"处理cookie弹窗时出错: {e}")

    def _scroll_to_load_content(self, page: PlaywrightPage, scroll_times: int = 3) -> None:
        """滚动页面以加载更多内容"""
        for i in range(scroll_times):
            print(f"滚动页面加载更多内容... ({i + 1}/{scroll_times})")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

    def _extract_urls_via_javascript(self, page: PlaywrightPage) -> Set[str]:
        """通过JavaScript提取文章链接"""
        urls = set()
        try:
            note_links = page.evaluate("""() => {
                const links = Array.from(document.querySelectorAll('a'));
                return links
                    .map(a => a.href)
                    .filter(href => href && (href.includes('/note/') || href.includes('xhslink')));
            }""")

            for link in note_links:
                urls.add(link)

        except Exception as e:
            print(f"JavaScript提取链接出错: {e}")

        return urls

    def _extract_urls_via_regex(self, page: PlaywrightPage) -> Set[str]:
        """通过正则表达式提取文章链接"""
        urls = set()
        try:
            content = page.content()
            patterns = [
                r'https://www\.xiaohongshu\.com/note/[a-zA-Z0-9]+',
                r'https://xhslink\.com/[a-zA-Z0-9]+',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    urls.add(match)
                    
        except Exception as e:
            print(f"正则提取链接出错: {e}")

        return urls

    def _extract_urls_from_network(self, page: PlaywrightPage) -> Set[str]:
        """从网络请求中提取文章链接"""
        urls = set()
        try:
            requests = page.evaluate("""() => {
                return performance.getEntriesByType('resource')
                    .filter(e => e.name.includes('note') || e.name.includes('xhslink'))
                    .map(e => e.name);
            }""")
            
            for req in requests:
                if '/note/' in req:
                    urls.add(req.split('?')[0])
                    
        except Exception as e:
            print(f"网络请求提取链接出错: {e}")

        return urls

    def _extract_article_cards(self, page: PlaywrightPage) -> List[Dict[str, Any]]:
        """提取页面中的文章卡片数据"""
        articles = []
        try:
            # 查找可能的文章卡片容器
            card_selectors = [
                '[data-v-0c549262]',
                '[data-v-7d75b457]',
                '.note-item',
                '.card',
                '.feed-item',
            ]
            
            for selector in card_selectors:
                try:
                    cards = page.locator(selector).all()
                    if cards:
                        print(f"找到 {len(cards)} 个卡片元素 (选择器: {selector})")
                        break
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"提取卡片出错: {e}")

        return articles

    def _search_page_action(self, page: PlaywrightPage) -> None:
        """搜索页面的自定义操作"""
        print("执行搜索页面自定义操作...")
        
        page.set_default_timeout(10000)
        print("设置页面默认超时为10秒")

        try:
            page.wait_for_load_state('domcontentloaded', timeout=10000)
            print("DOM内容加载完成")
        except Exception as e:
            print(f"等待DOM超时，继续执行: {e}")

        time.sleep(3)
        print("页面等待完成")

        self._handle_cookie_consent(page)
        time.sleep(1)

        self._scroll_to_load_content(page, scroll_times=4)
        time.sleep(2)

        # 使用多种策略提取URL
        print("\n开始提取文章链接...")
        urls1 = self._extract_urls_via_javascript(page)
        urls2 = self._extract_urls_via_regex(page)
        urls3 = self._extract_urls_from_network(page)
        
        all_urls = urls1.union(urls2).union(urls3)
        self._article_urls.update(all_urls)
        
        print(f"\n提取结果统计:")
        print(f"  JavaScript提取: {len(urls1)} 个")
        print(f"  正则提取: {len(urls2)} 个")
        print(f"  网络请求提取: {len(urls3)} 个")
        print(f"  总计唯一链接: {len(self._article_urls)} 个")
        
        for url in self._article_urls:
            print(f"  - {url}")

    def _parse_article_content(self, page: PlaywrightPage, url: str) -> Article:
        """解析文章页面内容"""
        time.sleep(2)

        title = ''
        title_selectors = ['h1', '.note-title', '[data-testid="note-title"]', '.title']
        for selector in title_selectors:
            try:
                title_elem = page.locator(selector).first
                if title_elem.is_visible(timeout=2000):
                    title = title_elem.text_content() or ''
                    if title:
                        break
            except Exception:
                continue

        content = ''
        content_selectors = ['.note-content', '[data-testid="note-content"]', '.desc', '.content', '[class*="desc"]']
        for selector in content_selectors:
            try:
                content_elem = page.locator(selector).first
                if content_elem.is_visible(timeout=2000):
                    content = content_elem.text_content() or ''
                    if content:
                        break
            except Exception:
                continue

        images = []
        try:
            img_elements = page.locator('img').all()
            for img in img_elements:
                src = img.get_attribute('src')
                if src and src.startswith('http') and ('xiaohongshu' in src or 'xhslink' in src or 'xhscdn' in src):
                    images.append(src)
        except Exception:
            pass

        author = ''
        author_selectors = ['.author-name', '.user-name', '[data-testid="user-name"]', '.username']
        for selector in author_selectors:
            try:
                author_elem = page.locator(selector).first
                if author_elem.is_visible(timeout=2000):
                    author = author_elem.text_content() or ''
                    if author:
                        break
            except Exception:
                continue

        publish_time = ''
        time_selectors = ['.publish-time', '.time', '[data-testid="publish-time"]', '.date']
        for selector in time_selectors:
            try:
                time_elem = page.locator(selector).first
                if time_elem.is_visible(timeout=2000):
                    publish_time = time_elem.text_content() or ''
                    if publish_time:
                        break
            except Exception:
                continue

        return Article(
            title=title.strip() if title else '',
            content=content.strip() if content else '',
            images=list(set(images)),
            author=author.strip() if author else '',
            url=url,
            publish_time=publish_time.strip() if publish_time else ''
        )

    def crawl(self, keyword: str, max_articles: int = 5) -> List[Article]:
        """主爬取方法"""
        articles = []
        self._article_urls.clear()
        self._article_data.clear()

        with StealthySession(
            headless=self.headless,
            solve_cloudflare=False,
            network_idle=False,
            timeout=self.timeout,
            block_images=False,
            block_media=False
        ) as session:
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_explore_feed"
            print(f"开始搜索: {search_url}")

            session.fetch(
                search_url,
                google_search=False,
                page_action=self._search_page_action,
                wait=3000
            )

            article_urls = list(self._article_urls)

            if not article_urls:
                print("未找到任何文章链接")
                return articles

            article_urls = article_urls[:max_articles]
            print(f"\n将爬取前 {len(article_urls)} 篇文章")

            for i, url in enumerate(article_urls, 1):
                try:
                    print(f"\n爬取第 {i}/{len(article_urls)} 篇文章: {url}")

                    article_data = [None]

                    def article_page_action(page: PlaywrightPage):
                        article_data[0] = self._parse_article_content(page, url)

                    session.fetch(url, page_action=article_page_action, wait=3000)

                    if article_data[0]:
                        article = article_data[0]
                        articles.append(article)

                        print(f"标题: {article.title or '未提取到'}")
                        print(f"作者: {article.author or '未提取到'}")
                        print(f"图片数量: {len(article.images)}")

                except Exception as e:
                    print(f"爬取文章失败 {url}: {e}")
                    continue

        return articles

    def save_results(self, articles: List[Article], filename: str = "xiaohongshu_results.json") -> None:
        """保存爬取结果到JSON文件"""
        results = []
        for article in articles:
            results.append({
                'title': article.title,
                'content': article.content,
                'images': article.images,
                'author': article.author,
                'url': article.url,
                'publish_time': article.publish_time
            })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {filename}")

def main():
    """主函数"""
    crawler = XiaohongshuAdvancedCrawler(
        headless=False,
        timeout=30000  # 30秒超时，单位：毫秒
    )

    keyword = "一加turbo6"

    articles = crawler.crawl(
        keyword=keyword,
        max_articles=5
    )

    print("\n" + "=" * 60)
    print("爬取结果摘要")
    print("=" * 60)
    for i, article in enumerate(articles, 1):
        print(f"\n{i}. 标题: {article.title or '无标题'}")
        print(f"   作者: {article.author or '未知'}")
        print(f"   图片: {len(article.images)} 张")
        print(f"   链接: {article.url}")
        if article.content:
            print(f"   内容预览: {article.content[:50]}..." if len(article.content) > 50 else f"   内容: {article.content}")

    if articles:
        crawler.save_results(articles)
    else:
        print("\n未能成功爬取到任何文章")

if __name__ == "__main__":
    main()
