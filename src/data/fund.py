# fund.py - 基金数据获取（净值、估值、持仓）
# 数据来源：天天基金 (fund.eastmoney.com / fundgz.1234567.com.cn)

import requests
import json
import re
import os
import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "http://fund.eastmoney.com/"
}

def get_realtime_estimate(fund_code):
    """获取基金盘中实时估值"""
    url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
    try:
        r = requests.get(url, timeout=10, headers=HEADERS)
        match = re.search(r"jsonpgz\((.+)\)", r.text)
        if match:
            data = json.loads(match.group(1))
            return {
                "fund_code": data["fundcode"],
                "name": data["name"],
                "estimate_value": float(data["gsz"]),
                "estimate_change_pct": float(data["gszzl"]),
                "estimate_time": data["gztime"],
                "net_value_date": data["jzrq"],
                "net_value": float(data["dwjz"]),
            }
    except Exception as e:
        return {"error": str(e)}
    return None

def get_net_value_history(fund_code, page=1, per_page=60):
    """获取基金历史净值"""
    url = (
        f"https://api.fund.eastmoney.com/f10/lsjz"
        f"?callback=jQuery&fundCode={fund_code}&pageIndex={page}"
        f"&pageSize={per_page}&startDate=&endDate=&_={int(__import__('time').time()*1000)}"
    )
    try:
        r = requests.get(url, timeout=10, headers={
            **HEADERS, "Referer": f"http://fund.eastmoney.com/f10/jjjz_{fund_code}.html"
        })
        match = re.search(r"jQuery\((.+)\)", r.text)
        if not match:
            return []
        data = json.loads(match.group(1))
        records = data.get("Data", {}).get("LSJZList", [])
        result = []
        for item in records:
            result.append({
                "date": item["FSRQ"],
                "net_value": float(item["DWJZ"]) if item["DWJZ"] else None,
                "daily_change_pct": float(item["JZZZL"]) if item["JZZZL"] else 0,
            })
        return result
    except Exception as e:
        return []

def get_holdings(fund_code):
    """获取基金前十大持仓（最新季报）"""
    url = (
        f"http://fundf10.eastmoney.com/FundArchivesDatas.aspx"
        f"?type=jjcc&code={fund_code}&topline=10&year=&month=&rt={__import__('time').time()}"
    )
    try:
        r = requests.get(url, timeout=10, headers=HEADERS)
        match = re.search(r"content:\"(.*)\"", r.text)
        if not match:
            return []
        html = match.group(1)
        # 提取每行持仓：股票代码、股票名称、占比
        pattern = (
            r"<td>\d+</td>"
            r"<td[^>]*><a[^>]+>(\w+)</a></td>"
            r"<td[^>]*><a[^>]+>([^<]+)</a>.*?"
            r"<td[^>]*>([\d.]+)%</td>"
        )
        matches = re.findall(pattern, html, re.DOTALL)
        holdings = []
        for code, name, ratio in matches:
            holdings.append({
                "code": code.strip(),
                "name": name.strip(),
                "ratio": float(ratio),
            })
        return holdings
    except Exception as e:
        return []

if __name__ == "__main__":
    code = "110011"
    print("=== 实时估值 ===")
    est = get_realtime_estimate(code)
    if est:
        print(f'{est["name"]} 估值: {est["estimate_value"]} ({est["estimate_change_pct"]}%)')
    print("=== 持仓 ===")
    holdings = get_holdings(code)
    for h in holdings:
        print(f'{h["name"]} ({h["code"]}): {h["ratio"]}%')
    print("=== 净值历史 ===")
    hist = get_net_value_history(code, page=1, per_page=5)
    for h in hist[:3]:
        print(f'{h["date"]}: {h["net_value"]} ({h["daily_change_pct"]}%)')
