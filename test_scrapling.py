"""
测试 Scrapling 基础功能
"""
from scrapling.fetchers import Fetcher, StealthyFetcher

# 测试基础 HTTP 请求
print("测试基础 HTTP 请求...")
try:
    page = Fetcher.get('https://quotes.toscrape.com/')
    quotes = page.css('.quote .text::text').getall()
    print(f"成功获取 {len(quotes)} 条名言")
    print(f"第一条: {quotes[0] if quotes else '无数据'}")
except Exception as e:
    print(f"错误: {e}")

print("\n测试完成!")
