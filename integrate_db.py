with open("D:/fund_monitor/app_v2.py", "r", encoding="utf-8-sig") as f:
    lines = f.readlines()

# 找插入点
insert_line = None
for i, l in enumerate(lines):
    if "# 缓存基金数据供 AI 管家使用" in l:
        insert_line = i
        break

if insert_line:
    db_block = [
        "# ======== 持久化到数据库 ========\n",
        "try:\n",
        "    from src.data.db import save_snapshot, save_ai_report, save_chat\n",
        "    for code, fd in all_funds_data.items():\n",
        '        est = fd.get("estimate")\n',
        '        if est and "error" not in est:\n',
        "            save_snapshot(\n",
        '                code, est.get("name"), est.get("estimate_value"),\n',
        '                est.get("estimate_change_pct"), est.get("net_value"),\n',
        '                est.get("net_value_date"), est.get("estimate_time")\n',
        "            )\n",
        '    if news_data and ai.api_key:\n',
        '        save_ai_report("market", \n',
        '            f"新闻{len(news_data)}条, 沪深300:{index_data}\n',
        '            , list(all_funds_data.keys()))\n',
        "except Exception:\n",
        "    pass  # 数据库写入失败不影响主流程\n",
        "\n",
    ]
    lines[insert_line:insert_line] = db_block

with open("D:/fund_monitor/app_v2.py", "w", encoding="utf-8") as f:
    f.writelines(lines)
print("db集成完成")
