# news.py - 新闻数据获取
# 数据源：新浪财经滚动新闻 + Playwright 百度搜索（备用）

import requests
import json
import datetime
import re

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# 新浪财经滚动新闻
SINA_ROLL_URL = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&num=30&page=1"

def fetch_market_news():
    """获取财经要闻（新浪滚动新闻）"""
    try:
        r = requests.get(SINA_ROLL_URL, timeout=10, headers=HEADERS)
        data = r.json()
        items = data.get("result", {}).get("data", [])
        news_list = []
        for item in items:
            news_list.append({
                "title": item.get("title", ""),
                "summary": item.get("summary", ""),
                "source": item.get("media_name", ""),
                "time": item.get("ctime", ""),
                "url": item.get("url", ""),
                "keywords": item.get("keywords", ""),
            })
        return news_list
    except Exception as e:
        return []

def filter_news_by_keywords(news_list, keywords):
    """过滤出包含指定关键词的新闻"""
    if not keywords:
        return news_list
    matched = []
    for news in news_list:
        text = (news.get("title", "") + " " + news.get("summary", "") + " " + news.get("keywords", "")).lower()
        for kw in keywords:
            if kw.lower() in text:
                matched.append(news)
                break
    return matched

def search_news_bing(keyword, max_results=10):
    """通过 Bing 搜索新闻（使用 Playwright 浏览器）"""
    from playwright.sync_api import sync_playwright
    results = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            search_url = f"https://cn.bing.com/news/search?q={keyword}&format=rss"
            page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
            # 尝试解析 XML
            content = page.content()
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(content)
                for item in root.findall(".//item")[:max_results]:
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    if title:
                        results.append({"title": title, "url": link, "source": "Bing"})
            except:
                pass
            browser.close()
    except Exception as e:
        pass
    return results

if __name__ == "__main__":
    print("=== 财经要闻 ===")
    news = fetch_market_news()
    for n in news[:5]:
        print(f'[{n["source"]}] {n["title"]}')
    
    print("\n=== 过滤基金相关 ===")
    matched = filter_news_by_keywords(news, ["基金", "A股", "股市", "市场"])
    for n in matched[:3]:
        print(f'{n["title"]}')
