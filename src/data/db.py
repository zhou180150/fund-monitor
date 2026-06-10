# db.py - SQLite 数据库层
# 独立模块，不依赖 app_v2.py 的 session_state
# 提供 fund_snapshots / daily_rankings / ai_reports / chat_logs 四张表

import sqlite3
import json
import os
import time
from datetime import datetime, timedelta

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "cache")
DB_PATH = os.path.join(DB_DIR, "fund_monitor.db")

# 保留天数
RETENTION = {
    "fund_snapshots": 30,
    "daily_rankings": 90,
    "ai_reports": 180,
    "chat_logs": 7,
}


def _get_conn():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db():
    """创建表（幂等）"""
    conn = _get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS fund_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fund_code TEXT NOT NULL,
        fund_name TEXT,
        estimate_value REAL,
        estimate_change_pct REAL,
        net_value REAL,
        net_value_date TEXT,
        estimate_time TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
    CREATE INDEX IF NOT EXISTS idx_snap_fund_time ON fund_snapshots(fund_code, created_at);

    CREATE TABLE IF NOT EXISTS daily_rankings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rank_date TEXT NOT NULL,
        rank_type TEXT NOT NULL,
        rank_data TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
    CREATE INDEX IF NOT EXISTS idx_rank_date ON daily_rankings(rank_date, rank_type);

    CREATE TABLE IF NOT EXISTS ai_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_type TEXT NOT NULL,
        content TEXT NOT NULL,
        fund_codes TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
    CREATE INDEX IF NOT EXISTS idx_report_type ON ai_reports(report_type, created_at);

    CREATE TABLE IF NOT EXISTS chat_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_message TEXT,
        ai_response TEXT,
        context TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
    """)
    conn.commit()
    conn.close()


# ======== 写入 ========

def save_snapshot(fund_code, fund_name, estimate_value, estimate_change_pct,
                  net_value=None, net_value_date=None, estimate_time=None):
    """保存一条估值快照"""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO fund_snapshots (fund_code, fund_name, estimate_value, "
        "estimate_change_pct, net_value, net_value_date, estimate_time) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (fund_code, fund_name, estimate_value, estimate_change_pct,
         net_value, net_value_date, estimate_time)
    )
    conn.commit()
    conn.close()


def save_ranking(rank_type, rank_data):
    """保存排行榜快照（rank_data 传 list/dict 会自动 JSON 序列化）"""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO daily_rankings (rank_date, rank_type, rank_data) VALUES (?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d"), rank_type, json.dumps(rank_data, ensure_ascii=False))
    )
    conn.commit()
    conn.close()


def save_ai_report(report_type, content, fund_codes=None):
    """保存 AI 分析报告"""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO ai_reports (report_type, content, fund_codes) VALUES (?, ?, ?)",
        (report_type, content if isinstance(content, str) else json.dumps(content, ensure_ascii=False),
         ",".join(fund_codes) if fund_codes else None)
    )
    conn.commit()
    conn.close()


def save_chat(user_message, ai_response, context=None):
    """保存聊天记录"""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO chat_logs (user_message, ai_response, context) VALUES (?, ?, ?)",
        (user_message, ai_response, json.dumps(context, ensure_ascii=False) if context else None)
    )
    conn.commit()
    conn.close()


# ======== 查询 ========

def get_recent_snapshots(fund_code, days=30):
    """获取最近 N 天的估值快照"""
    conn = _get_conn()
    cursor = conn.execute(
        "SELECT * FROM fund_snapshots WHERE fund_code = ? "
        "AND created_at >= datetime('now', ? || ' days', 'localtime') "
        "ORDER BY created_at ASC",
        (fund_code, f"-{days}")
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_latest_rankings(rank_type=None, days=30):
    """获取最近的排行榜"""
    conn = _get_conn()
    sql = "SELECT * FROM daily_rankings WHERE created_at >= datetime('now', ?, 'localtime')"
    params = [f"-{days}"]
    if rank_type:
        sql += " AND rank_type = ?"
        params.append(rank_type)
    sql += " ORDER BY created_at DESC"
    cursor = conn.execute(sql, params)
    rows = [dict(r) for r in cursor.fetchall()]
    for r in rows:
        try:
            r["rank_data"] = json.loads(r["rank_data"])
        except:
            pass
    conn.close()
    return rows


def get_recent_reports(report_type=None, days=30):
    """获取最近的分析报告"""
    conn = _get_conn()
    sql = "SELECT * FROM ai_reports"
    params = []
    conditions = ["created_at >= datetime('now', ?, 'localtime')"]
    params.append(f"-{days}")
    if report_type:
        conditions.append("report_type = ?")
        params.append(report_type)
    sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY created_at DESC"
    cursor = conn.execute(sql, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ======== 维护 ========

def cleanup():
    """清理过期数据"""
    conn = _get_conn()
    for table, days in RETENTION.items():
        conn.execute(
            f"DELETE FROM {table} WHERE created_at < datetime('now', ?, 'localtime')",
            (f"-{days}",)
        )
    conn.commit()
    conn.close()


def get_stats():
    """数据库统计"""
    conn = _get_conn()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r["name"] for r in cursor.fetchall()]
    stats = {"tables": tables, "size_kb": 0, "rows": {}}
    if os.path.exists(DB_PATH):
        stats["size_kb"] = round(os.path.getsize(DB_PATH) / 1024, 1)
    for t in tables:
        if t.startswith("sqlite"):
            continue
        cursor = conn.execute(f"SELECT COUNT(*) as cnt FROM {t}")
        stats["rows"][t] = cursor.fetchone()["cnt"]
    conn.close()
    return stats


# 初始化（模块首次加载时自动建表）
init_db()
