with open("D:/fund_monitor/app_v2.py", "r", encoding="utf-8-sig") as f:
    text = f.read()

old = """# ======== 持久化到数据库 ========
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
except Exception as e:
    import sys; print(f\"[DB ERROR] {e}\", file=sys.stderr)"""

new = """# ======== 持久化到数据库 ========
from src.data.db import save_snapshot
for code, fd in all_funds_data.items():
    est = fd.get("estimate")
    if est and "error" not in est and est.get("estimate_value") is not None:
        save_snapshot(
            code, est.get("name"),
            est.get("estimate_value"),
            est.get("estimate_change_pct"),
            est.get("net_value"),
            est.get("net_value_date"),
            est.get("estimate_time")
        )"""

text = text.replace(old, new)

with open("D:/fund_monitor/app_v2.py", "w", encoding="utf-8") as f:
    f.write(text)
print("done")
