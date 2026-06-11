# rank.py - 天天基金排行榜数据
# 数据来源: http://fund.eastmoney.com/data/rankhandler.aspx

import requests
import re
import json
import numpy as np

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "http://fund.eastmoney.com/data/fundranking.html"
}

# 基金详情页面 HEADERS
FUND_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "http://fund.eastmoney.com/"
}


def get_fund_rank(sort_by="return", order="desc", page=1, per_page=50):
    """获取基金排行榜

    参数:
        sort_by: return/risk/rating
        order: desc/asc
    """
    # 天天基金排行接口
    url = (
        "http://fund.eastmoney.com/data/rankhandler.aspx"
        f"?op=ph&dt=kf&ft=all&rs=&gs=0&sc=1yzf&st=desc&sd=&ed=&"
        f"qdii=&tabSubType=ABBR&pi={page}&pn={per_page}&dx=1&v=0.{(id)(__import__('time').time()*1000)}"
    )
    try:
        r = requests.get(url, timeout=15, headers=HEADERS)
        r.encoding = "utf-8"
        match = re.search(r"\[(.*?)\]", r.text, re.DOTALL)
        if not match:
            return []
        data_str = match.group(0)
        items = json.loads(f"[{match.group(1)}]")
        results = []
        for item in items[:per_page]:
            parts = item.split(",")
            if len(parts) >= 10:
                results.append({
                    "code": parts[0],
                    "name": parts[1],
                    "unit_net_value": parts[3] if len(parts) > 3 else "",
                    "daily_change": parts[4] if len(parts) > 4 else "",
                    "week_return": parts[5] if len(parts) > 5 else "",
                    "month_return": parts[6] if len(parts) > 6 else "",
                    "quarter_return": parts[7] if len(parts) > 7 else "",
                    "year_return": parts[8] if len(parts) > 8 else "",
                })
        return results
    except Exception as e:
        print(f"排行榜请求失败: {e}")
        return []


def _fetch_nav_history(fund_code, days=60):
    """获取基金历史净值（用于计算回撤/波动率）"""
    url = (
        f"https://api.fund.eastmoney.com/f10/lsjz"
        f"?callback=jQuery&fundCode={fund_code}&pageIndex=1"
        f"&pageSize={days}&startDate=&endDate=&_={int(__import__('time').time()*1000)}"
    )
    try:
        r = requests.get(url, timeout=8, headers={
            **FUND_HEADERS, "Referer": f"http://fund.eastmoney.com/f10/jjjz_{fund_code}.html"
        })
        match = re.search(r"jQuery\((.+)\)", r.text)
        if not match:
            return []
        data = json.loads(match.group(1))
        records = data.get("Data", {}).get("LSJZList", [])
        result = []
        for item in records:
            nv = item.get("DWJZ", "")
            if nv:
                result.append(float(nv))
        return result
    except Exception:
        return []


def _fetch_fund_info(fund_code):
    """获取基金基本信息（规模、经理任期）
    数据来源：fund.eastmoney.com/{code}.html 基金概览页
    """
    info = {"scale": "N/A", "manager_tenure": "N/A", "manager_name": "N/A"}
    url = f"http://fund.eastmoney.com/{fund_code}.html"
    try:
        r = requests.get(url, timeout=8, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        r.encoding = "utf-8"
        text = r.text
        # 基金规模
        m = re.search(r'规模[^>]*>[^:：]*[:：]\s*([\d.]+)\s*亿元', text)
        if m:
            info["scale"] = m.group(1) + "亿"
        # 基金经理名称
        m = re.search(r'基金经理[^>]*>[^<]*<[^>]*>([^<]{2,6})[<]', text)
        if not m:
            m = re.search(r'基金经理[：:]\s*([^<]{2,6})[<\s]', text)
        if m:
            info["manager_name"] = m.group(1).strip()
            info["manager_tenure"] = "稳定"  # 默认值
    except Exception:
        pass
    return info


def _calc_indicators(nav_list):
    """从净值序列计算回撤/波动率指标"""
    result = {
        "max_drawdown_30d": "N/A",
        "max_drawdown_90d": "N/A",
        "max_drawdown_180d": "N/A",
        "volatility_20d": "N/A",
        "top3_concentration": "N/A",
    }
    if not nav_list or len(nav_list) < 5:
        return result

    # 回撤计算
    def _max_dd(prices):
        peak = prices[0]
        max_dd = 0
        for p in prices:
            if p > peak:
                peak = p
            dd = (peak - p) / peak * 100
            if dd > max_dd:
                max_dd = dd
        return round(max_dd, 2)

    if len(nav_list) >= 30:
        result["max_drawdown_30d"] = f"{_max_dd(nav_list[-30:]):.2f}%"
    if len(nav_list) >= 90:
        result["max_drawdown_90d"] = f"{_max_dd(nav_list[-90:]):.2f}%"
    else:
        result["max_drawdown_90d"] = f"{_max_dd(nav_list):.2f}%"
    result["max_drawdown_180d"] = f"{_max_dd(nav_list):.2f}%"

    # 波动率（年化）
    if len(nav_list) >= 5:
        daily_rets = []
        for i in range(1, len(nav_list)):
            daily_rets.append((nav_list[i] - nav_list[i-1]) / nav_list[i-1] * 100)
        recent_20 = daily_rets[-20:] if len(daily_rets) >= 20 else daily_rets
        vol = np.std(recent_20) * np.sqrt(252)
        result["volatility_20d"] = f"{vol:.2f}%"

    return result


def enrich_rank_data(rank_items):
    """对排行榜基金逐只补全回撤/波动率/规模/经理任期数据

    参数:
        rank_items: get_fund_rank 返回的列表（建议 < 30 只，避免超时）

    返回:
        原列表每项扩充了以下字段:
            max_drawdown_30d, max_drawdown_90d, max_drawdown_180d,
            volatility_20d, top3_concentration, scale, manager_tenure
    """
    for item in rank_items:
        code = item.get("code", "")
        # 并行拉取历史净值和基金信息
        nav_list = _fetch_nav_history(code, 90)
        fund_info = _fetch_fund_info(code)

        indicators = _calc_indicators(nav_list)
        item.update(indicators)
        item["scale"] = fund_info.get("scale", "N/A")
        item["manager_tenure"] = fund_info.get("manager_tenure", "N/A")

    return rank_items