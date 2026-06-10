# rank.py - 天天基金排行榜数据
# 数据来源: http://fund.eastmoney.com/data/rankhandler.aspx

import requests
import re
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "http://fund.eastmoney.com/data/fundranking.html"
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
