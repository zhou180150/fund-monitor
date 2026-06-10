# stock.py - 个股行情数据获取
# 数据来源：腾讯证券 qt.gtimg.cn

import requests
import datetime

HEADERS = {"User-Agent": "Mozilla/5.0"}

def _get_tencent_symbol(code):
    """将纯数字代码转换为腾讯接口前缀"""
    code = str(code).strip()
    # 沪深300等指数代码白名单
    if code in ("000300", "399300", "399001", "399006", "000001", "000016", "000688", "000905"):
        return "sh" + code if not code.startswith("000001") else "sh000001"
    # 如果已经带了sh/sz前缀，直接返回
    if code.startswith(("sh", "sz", "SH", "SZ")):
        return code.lower()
    if code.startswith(("6", "9")):
        return f"sh{code}"
    elif code.startswith(("0", "3", "1")):
        return f"sz{code}"
    else:
        # 指数代码一般000xxx开头但走sh
        return f"sh{code}"

def _parse_tencent_response(text):
    """解析腾讯行情单条返回"""
    parts = text.split('"', 1)
    if len(parts) < 2:
        return None
    fields = parts[1].split("~")
    if len(fields) < 35:
        return None
    return {
        "name": fields[1].strip(),
        "code": fields[2].strip(),
        "price": float(fields[3]) if fields[3] else 0,
        "prev_close": float(fields[4]) if fields[4] else 0,
        "open": float(fields[5]) if fields[5] else 0,
        "volume": int(fields[6]) if fields[6] else 0,
        "change_pct": float(fields[32]) if fields[32] else 0,
        "change_amount": float(fields[31]) if fields[31] else 0,
        "high": float(fields[33]) if fields[33] else 0,
        "low": float(fields[34]) if fields[34] else 0,
        "time": fields[30],
    }

def get_stock_realtime(stock_codes):
    """批量获取个股实时行情"""
    if isinstance(stock_codes, str):
        stock_codes = [stock_codes]
    results = []
    for code in stock_codes:
        symbol = _get_tencent_symbol(code)
        try:
            r = requests.get(f"http://qt.gtimg.cn/q={symbol}", timeout=10, headers=HEADERS)
            r.encoding = "GBK"
            parsed = _parse_tencent_response(r.text)
            if parsed:
                results.append(parsed)
        except Exception as e:
            results.append({"code": code, "error": str(e)})
    return results

def get_index_realtime(index_code="sh000300"):
    """获取大盘指数实时行情"""
    return get_stock_realtime([index_code])

def get_stock_kline(stock_code, days=60):
    """获取个股日K线"""
    symbol = _get_tencent_symbol(stock_code)
    try:
        r = requests.get(
            f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,{days},qfq",
            timeout=10, headers=HEADERS
        )
        data = r.json()
        stock_data = data.get("data", {}).get(symbol, {})
        klines = stock_data.get("day") or stock_data.get("qfqday") or []
        results = []
        for k in klines:
            results.append({
                "date": k[0],
                "open": float(k[1]),
                "close": float(k[2]),
                "high": float(k[3]),
                "low": float(k[4]),
                "volume": int(float(k[5])) if len(k) > 5 and k[5] else 0,
            })
        return results
    except Exception as e:
        return []

if __name__ == "__main__":
    print("=== ???? ===")
    stocks = get_stock_realtime(["600519", "000858"])
    for s in stocks:
        if "error" in s:
            print("ERROR:", s["error"])
        else:
            print(f'{s["name"]} ({s["code"]}): {s["price"]} ({s["change_pct"]}%)')
    print("=== ???? ===")
    idx = get_index_realtime("sh000300")
    for i in idx:
        if "error" in i:
            print("ERROR:", i["error"])
        else:
            print(f'{i["name"]}: {i["price"]} ({i["change_pct"]}%)')
    print("=== K? ===")
    for code in ["000858", "600519"]:
        kline = get_stock_kline(code, 5)
        print(f'{code}: {len(kline)} bars, latest: {kline[0]["date"] if kline else "N/A"}')