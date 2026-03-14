#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书爬虫脚本 - 使用 Scrapling 框架
爬取搜索结果页面的文章图文内容
"""
import os
import json
import time
from typing import List, Dict
from urllib.parse import urljoin, quote

from scrapling.fetchers import StealthySession, StealthyFetcher
from scrapling.core.custom_types import Adaptor


class XiaohongshuCrawler:
    """小红书爬虫类"""
    
    def __init__(self, save_dir: str = "xiaohongshu_data"):
        """
        初始化爬虫
        :param save_dir: 数据保存目录
        """
        self.save_dir = save_dir
        self.base_url = "https://www.xiaohongshu.com"
        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)
        os.makedirs(os.path.join(save_dir, "images"), exist_ok=True)
        
    def search_keyword(self, keyword: str, max_pages: int = 5) -> List[Dict]:
        """
        搜索关键词并获取笔记列表
        :param keyword: 搜索关键词
        :param max_pages: 最大翻页数
        :return: 笔记列表
        """
        # 对关键词进行 URL 编码
        encoded_keyword = quote(keyword)
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web_explore_feed"
        
        print(f"开始搜索: {keyword}")
        print(f"搜索URL: {search_url}")
        
        notes = []
        
        # 使用 StealthySession 访问
        with StealthySession(
            headless=False,  # 显示浏览器以便调试
            solve_cloudflare=True,
            wait_for_selector=".note-item",
            timeout=60000,
        ) as session:
            try:
                # 访问搜索页面
                page = session.fetch(
                    search_url,
                    wait_for_selector=".note-item",
                    google_search=False,
                )
                
                print(f"页面状态码: {page.status}")
                print(f"页面标题: {page.css('title::text').get() or '无标题'}")
                
                # 等待页面加载完成
                time.sleep(5)
                
                # 获取笔记卡片
                note_cards = page.css(".note-item")
                print(f"找到 {len(note_cards)} 个笔记卡片")
                
                # 解析笔记卡片
                for i, card in enumerate(note_cards[:20]):  # 限制数量
                    try:
                        note_data = self._parse_note_card(card)
                        if note_data:
                            notes.append(note_data)
                            print(f"解析笔记 {i+1}: {note_data.get('title', '无标题')}")
                    except Exception as e:
                        print(f"解析笔记卡片 {i} 出错: {e}")
                
                # 获取页面内容用于调试
                with open(os.path.join(self.save_dir, "debug_page.html"), "w", encoding="utf-8") as f:
                    f.write(page.text)
                    
            except Exception as e:
                print(f"访问搜索页面出错: {e}")
                import traceback
                traceback.print_exc()
        
        return notes
    
    def _parse_note_card(self, card: Adaptor) -> Dict:
        """解析笔记卡片"""
        # 获取链接
        link = card.css("a::attr(href)").get()
        if link:
            if not link.startswith("http"):
                link = urljoin(self.base_url, link)
        
        # 获取标题
        title = card.css("h3::text").get() or card.css(".title::text").get()
        if not title:
            # 尝试其他选择器
            title = card.css('[class*="title"]::text').get()
        
        # 获取封面图
        cover = card.css("img::attr(src)").get()
        
        # 获取作者
        author = card.css(".author::text").get() or card.css('[class*="author"]::text').get()
        
        # 获取点赞/收藏数
        likes = card.css(".like::text").get() or card.css('[class*="like"]::text').get()
        
        return {
            "title": title.strip() if title else "无标题",
            "link": link,
            "cover": cover,
            "author": author.strip() if author else "未知",
            "likes": likes.strip() if likes else "0",
        }
    
    def get_note_detail(self, url: str) -> Dict:
        """获取笔记详情"""
        print(f"获取笔记详情: {url}")
        
        with StealthySession(
            headless=False,
            solve_cloudflare=True,
            timeout=60000,
        ) as session:
            try:
                page = session.fetch(
                    url,
                    wait_for_selector=".note-content",
                    google_search=False,
                )
                
                time.sleep(3)
                
                # 保存页面用于调试
                with open(os.path.join(self.save_dir, "note_detail.html"), "w", encoding="utf-8") as f:
                    f.write(page.text)
                
                # 提取标题
                title = page.css(".note-title::text").get() or page.css("h1::text").get()
                
                # 提取内容
                content = page.css(".note-content::text").getall()
                content = "\n".join([c.strip() for c in content if c.strip()])
                
                # 提取图片
                images = page.css(".note-content img::attr(src)").getall()
                if not images:
                    images = page.css("img::attr(src)").getall()
                
                # 下载图片
                local_images = []
                for i, img_url in enumerate(images[:10]):  # 限制图片数量
                    try:
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        local_path = self._download_image(img_url, f"note_{int(time.time())}_{i}")
                        if local_path:
                            local_images.append(local_path)
                    except Exception as e:
                        print(f"下载图片出错: {e}")
                
                return {
                    "url": url,
                    "title": title.strip() if title else "无标题",
                    "content": content,
                    "images": local_images,
                    "raw_images": images,
                }
                
            except Exception as e:
                print(f"获取笔记详情出错: {e}")
                import traceback
                traceback.print_exc()
                return {}
    
    def _download_image(self, url: str, filename: str) -> str:
        """下载图片"""
        if not url:
            return ""
        
        try:
            # 使用 Fetcher 下载图片
            from scrapling.fetchers import Fetcher
            response = Fetcher.get(url, stealthy_headers=True)
            
            if response.status == 200:
                # 确定文件扩展名
                ext = ".jpg"
                if ".png" in url.lower():
                    ext = ".png"
                elif ".gif" in url.lower():
                    ext = ".gif"
                elif ".webp" in url.lower():
                    ext = ".webp"
                
                filepath = os.path.join(self.save_dir, "images", f"{filename}{ext}")
                with open(filepath, "wb") as f:
                    f.write(response.content)
                return filepath
        except Exception as e:
            print(f"下载图片失败 {url}: {e}")
        return ""
    
    def save_data(self, data: List[Dict], filename: str = "search_results.json"):
        """保存数据到 JSON 文件"""
        filepath = os.path.join(self.save_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到: {filepath}")


def main():
    """主函数"""
    # 搜索关键词
    keyword = "一加turbo6"
    
    # 创建爬虫实例
    crawler = XiaohongshuCrawler()
    
    # 1. 搜索笔记
    print("=" * 60)
    print("第一步: 搜索笔记")
    print("=" * 60)
    notes = crawler.search_keyword(keyword, max_pages=3)
    
    print(f"\n找到 {len(notes)} 条笔记")
    for i, note in enumerate(notes):
        print(f"{i+1}. {note.get('title')} - {note.get('link')}")
    
    # 保存搜索结果
    crawler.save_data(notes, "search_results.json")
    
    # 2. 获取前3条笔记的详情
    print("\n" + "=" * 60)
    print("第二步: 获取笔记详情")
    print("=" * 60)
    
    detailed_notes = []
    for note in notes[:3]:
        if note.get("link"):
            detail = crawler.get_note_detail(note["link"])
            detailed_notes.append({**note, **detail})
            time.sleep(2)
    
    # 保存详情
    crawler.save_data(detailed_notes, "detailed_notes.json")
    
    print("\n" + "=" * 60)
    print("爬取完成!")
    print(f"共获取 {len(notes)} 条笔记，{len(detailed_notes)} 条详情")
    print(f"数据保存在: {crawler.save_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
