"""
测试 StealthyFetcher
"""
from scrapling.fetchers import StealthyFetcher

print("测试 StealthyFetcher...")
try:
    # 使用 headless 模式测试
    page = StealthyFetcher.fetch('https://quotes.toscrape.com/', headless=True)
    quotes = page.css('.quote .text::text').getall()
    print(f"成功获取 {len(quotes)} 条名言")
    print(f"第一条: {quotes[0] if quotes else '无数据'}")
except Exception as e:
    print(f"错误: {e}")

print("\n测试完成!")
