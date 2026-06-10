with open("D:/fund_monitor/app_v2.py", "r", encoding="utf-8-sig") as f:
    text = f.read()

old_block = """# ======== 持久化到数据库 ========
try:
    from src.data.db import save_snapshot, save_ai_report, save_chat
    for code, fd in all_funds_data.items():
        est = fd.get("estimate")
        if est and "error" not in est:
            save_snapshot(
                code, est.get("name"), est.get("estimate_value"),
                est.get("estimate_change_pct"), est.get("net_value"),
                est.get("net_value_date"), est.get("estimate_time")
            )
    if news_data and ai.api_key:
        save_ai_report("market", 
            f"新闻{len(news_data)}条, 沪深300:{index_data}
            , list(all_funds_data.keys()))
except Exception:
    pass  # 数据库写入失败不影响主流程"""

new_block = """# ======== 持久化到数据库 ========
try:
    from src.data.db import save_snapshot
    for code, fd in all_funds_data.items():
        est = fd.get("estimate")
        if est and "error" not in est:
            save_snapshot(
                code, est.get("name"),
                est.get("estimate_value"),
                est.get("estimate_change_pct"),
                est.get("net_value"),
                est.get("net_value_date"),
                est.get("estimate_time")
            )
except Exception:
    pass"""

text = text.replace(old_block, new_block)

with open("D:/fund_monitor/app_v2.py", "w", encoding="utf-8") as f:
    f.write(text)
print("fixed")
