# push.py - 推送模块（为后续飞书/邮件推送预留）
# 当前版本：仅生成推送内容，尚未集成实际发送

import json
import os
from datetime import datetime


def generate_push_report(db_stats, funds_data, ai_report):
    """生成推送报告内容"""
    lines = []
    lines.append(f"=== 基金日报 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    lines.append(f"数据统计: {db_stats}")
    lines.append("")

    if ai_report:
        risk = ai_report.get("risk", "")
        market = ai_report.get("market", "")
        if risk:
            lines.append(f"【风险分析】\n{risk}")
        if market:
            lines.append(f"【市场分析】\n{market}")

    for code, fd in funds_data.items():
        est = fd.get("estimate")
        if est and "error" not in est:
            name = est.get("name", code)
            chg = est.get("estimate_change_pct", "N/A")
            lines.append(f"{name}: {chg}%")

    return "\n".join(lines)


# ======== 后续实现计划 ========
# 1. 飞书推送：使用 lark-cli 或飞书自定义机器人 Webhook
#    - 创建群聊机器人 Webhook URL
#    - 每日 9:30 开盘推送市场前瞻
#    - 每日 15:30 收盘推送基金日报
#    - 风险预警：当回撤超阈值时实时推送
# 
# 2. 邮件推送：使用 SMTP
#    - 集成到 app_v2.py 的定时任务
#    - 通过 APScheduler 或 Streamlit 的自动刷新触发
#
# 3. 推送格式：
#    - 标题：[基金提醒] 你的基金需要关注
#    - 内容模板：包含风险等级、涨跌幅、市场情绪、操作建议
#    - 链接：直接跳转到 Streamlit 看板
