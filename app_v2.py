# app_v2.py - 基金监控看板入口
# 运行: streamlit run app_v2.py

import streamlit as st
import json
import os
import sys
import time
import threading
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.fund import get_realtime_estimate, get_net_value_history, get_holdings
from src.data.stock import get_stock_realtime, get_index_realtime, get_stock_kline
from src.data.news import fetch_market_news, filter_news_by_keywords
from src.analysis.advisor import AIAdvisor
from src.pages.watch import render_watch_page
from src.pages.review import render_review_page
from src.pages.compare import render_compare_page
from src.pages.recommend import render_recommend_page
from src.data.db import save_snapshot, save_chat, save_ai_report, cleanup, get_stats

# 页面配置
GLOBAL_CSS = """
<style>
    .stApp { background-color: #0e1117; }
    .stApp header { background-color: #0e1117; }
    section[data-testid="stSidebar"] {
        background-color: #11141c;
        border-right: 1px solid #1a1d29;
    }
    section[data-testid="stSidebar"] * {
        color: #c5c8d4 !important;
    }
    section[data-testid="stSidebar"] .st-caption {
        color: #8892b0 !important;
        font-size: 12px !important;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] .st-emotion-cache-vmpjyt {
        color: #e6e9f0 !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] .st-emotion-cache-1aehpvj {
        color: #8892b0 !important;
        font-size: 13px !important;
    }
    div[data-testid="metric-container"] {
        background: #1a1d29;
        border: 1px solid #2a2d3a;
        border-radius: 10px;
        padding: 12px 16px;
    }
    div[data-testid="metric-container"] label {
        color: #8892b0 !important;
        font-size: 13px !important;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #e6e9f0 !important;
        font-size: 26px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stDataFrame"] th {
        background: #1a1d29 !important;
        color: #8892b0 !important;
        font-weight: 500 !important;
    }
    div[data-testid="stDataFrame"] td {
        color: #c5c8d4 !important;
        border-bottom: 1px solid #1a1d29 !important;
    }
    div.stButton button {
        background: #1a1d29;
        border: 1px solid #2a2d3a;
        color: #e6e9f0;
        border-radius: 8px;
    }
    div.stButton button:hover {
        border-color: #64b5f6;
    }
    div[role="radiogroup"] label {
        background: #1a1d29 !important;
        border: 1px solid #2a2d3a !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        color: #8892b0 !important;
    }
    div[role="radiogroup"] label[data-checked="true"] {
        background: #202430 !important;
        border-color: #64b5f6 !important;
        color: #e6e9f0 !important;
    }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0e1117; }
    ::-webkit-scrollbar-thumb { background: #2a2d3a; border-radius: 3px; }
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] { min-width: 100% !important; }
        div[data-testid="metric-container"] { padding: 8px 10px !important; }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] { font-size: 20px !important; }
    }
</style>
"""

st.set_page_config(
    page_title="基金监控看板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# 加载配置
@st.cache_data(ttl=60)
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

config = load_config()
funds = config.get("funds", [])
benchmark = config.get("benchmark", "sh000300")

# DeepSeek 初始化（优先从环境变量取，兼容 Streamlit Cloud Secrets）
deepseek_key = os.getenv("DEEPSEEK_API_KEY", config.get("deepseek_api_key", ""))
ai = AIAdvisor(deepseek_key)

# ============================================
# 数据加载函数
# ============================================

@st.cache_data(ttl=120, show_spinner=False)
def load_fund_data(fund_code):
    estimate = get_realtime_estimate(fund_code)
    history = get_net_value_history(fund_code, page=1, per_page=60)
    holdings = get_holdings(fund_code)
    return {
        "estimate": estimate,
        "history": history,
        "holdings": holdings,
        "name": estimate["name"] if estimate and "name" in estimate else fund_code,
    }

@st.cache_data(ttl=60, show_spinner=False)
def load_all_stock_data(all_codes):
    if not all_codes:
        return []
    return get_stock_realtime(list(set(all_codes)))

@st.cache_data(ttl=120, show_spinner=False)
def load_index_data():
    return get_index_realtime(benchmark)

@st.cache_data(ttl=120, show_spinner=False)
def load_index_history():
    return get_stock_kline("sh000300", 60)

@st.cache_data(ttl=300, show_spinner=False)
def load_news_data(keywords=None):
    news = fetch_market_news()
    if keywords:
        news = filter_news_by_keywords(news, keywords)
    return news

# ============================================
# 侧边栏
# ============================================

st.sidebar.title("📊 基金监控")
st.sidebar.caption(f"交易日 {date.today()}")

# 清理按钮
with st.sidebar.popover("⚙️ 设置", use_container_width=True):
    if st.button("🧹 清理过期数据"):
        try:
            cleanup()
            st.toast("已清理过期数据", icon="✅")
        except Exception as e:
            st.toast(f"清理失败: {e}", icon="❌")
    if st.button("📊 数据库统计"):
        stats = get_stats()
        st.json(stats)

page = st.sidebar.radio("导航", ["📡 盯盘", "📊 复盘", "⚖️ 对比", "🎯 推荐"], horizontal=True)

if st.sidebar.button("🔄 刷新数据", use_container_width=True):
    st.cache_data.clear()

st.sidebar.divider()
st.sidebar.caption("当前关注:")
for f in funds:
    st.sidebar.markdown(f"**{f['name']}** ({f['code']})")

# ============================================
# AI 管家聊天区
# ============================================

st.sidebar.divider()
st.sidebar.markdown(
    "<div style='font-size:14px;font-weight:600;color:#64b5f6;margin:4px 0'>🤖 AI 管家</div>",
    unsafe_allow_html=True
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "我是 AI 基金管家，随时为你分析持仓、市场或推荐基金。"}
    ]

# 快捷问题
quick_qs = ["我的基金风险如何", "今天市场怎么样", "这个位置该不该加仓"]
qs_keys = ["risk", "market", "position"]
cols = st.sidebar.columns(3)
for i, q in enumerate(quick_qs):
    with cols[i]:
        if st.button(q[:4], key=f"qq_{i}", use_container_width=True):
            st.session_state._quick_q = qs_keys[i]

# 聊天输入
user_input = st.sidebar.chat_input("问我任何基金问题...")

# 处理快捷提问
quick_trigger = st.session_state.pop("_quick_q", None)
if quick_trigger:
    q_map = {"risk": "我的基金风险如何，请给出风险等级和操作建议", "market": "今天市场怎么样，情绪如何", "position": "这个位置该不该加仓"}
    user_input = q_map.get(quick_trigger, "")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    with st.spinner("AI 思考中..."):
        try:
            fd_cache = st.session_state.get("_funds_cache", {})
            ns_cache = st.session_state.get("_news_cache", [])
            ix_cache = st.session_state.get("_index_cache", [])
            fund_lines = "\n".join([f"- {v.get('name',k) if v else k}" for k, v in fd_cache.items()])
            idx_line = ""
            if ix_cache:
                i = ix_cache[0] if isinstance(ix_cache, list) else ix_cache
                if i and "error" not in i:
                    idx_line = f"\n沪深300: {i.get('price','')} ({i.get('change_pct','')}%)"
            ctx = f"用户持仓:\n{fund_lines}{idx_line}\n\n新闻: {len(ns_cache)}条今天的\n\n问题: {user_input}"
            resp = ai.call_api(
                "你是一个专业的中国基金分析管家，回答简洁有依据。",
                ctx, max_tokens=500
            )
            st.session_state.chat_history.append({"role": "assistant", "content": resp})
            # 保存到数据库
            try:
                save_chat(user_input, resp, {"funds": list(fd_cache.keys())})
            except Exception as db_err:
                st.toast(f"聊天记录保存失败: {db_err}", icon="⚠️")
        except Exception as e:
            err_msg = f"[分析失败: {e}]"
            st.session_state.chat_history.append({"role": "assistant", "content": err_msg})
            try:
                save_chat(user_input, err_msg)
            except Exception:
                pass
    st.rerun()

# 聊天显示区
with st.sidebar.expander("💬 对话记录", expanded=True):
    for msg in st.session_state.chat_history[-8:]:
        if msg["role"] == "assistant":
            st.markdown(
                f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:10px;padding:10px;
                margin-bottom:6px;font-size:12px;line-height:1.5;color:#c5c8d4">{msg["content"][:300]}</div>""",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""<div style="text-align:right;padding:6px 10px;margin-bottom:4px;font-size:12px;color:#8892b0">
                你：{msg["content"][:80]}</div>""",
                unsafe_allow_html=True
            )

st.sidebar.caption("Powered by DeepSeek")

# ============================================
# 数据加载
# ============================================

if not funds:
    st.error("请在 config.json 中添加关注的基金代码")
    st.stop()

all_funds_data = {}
all_stock_codes = []
news_keywords = ["基金", "A股", "市场", "股市", "行情", "投资"]

with st.spinner("加载数据中..."):
    def _load_one(code):
        return code, load_fund_data(code)

    fund_codes = [f["code"] for f in funds]
    with ThreadPoolExecutor(max_workers=min(len(fund_codes), 4)) as pool:
        futures = {pool.submit(_load_one, code): code for code in fund_codes}
        for future in as_completed(futures):
            code, fund_data = future.result()
            all_funds_data[code] = fund_data
            if fund_data.get("holdings"):
                for h in fund_data["holdings"]:
                    all_stock_codes.append(h["code"])

    # 并行加载行情 & 新闻
    def _load_extra():
        codes = list(set(all_stock_codes))
        results = {}
        def _get_stocks():
            results["stocks"] = load_all_stock_data(codes) if codes else []
        def _get_index():
            results["idx"] = load_index_data()
        def _get_kline():
            results["kline"] = load_index_history()
        def _get_news():
            results["news"] = load_news_data(keywords=news_keywords)
        threads = [
            threading.Thread(target=_get_stocks, daemon=True),
            threading.Thread(target=_get_index, daemon=True),
            threading.Thread(target=_get_kline, daemon=True),
            threading.Thread(target=_get_news, daemon=True),
        ]
        for t in threads: t.start()
        for t in threads: t.join(timeout=15)
        return (results.get("stocks", []), results.get("idx", []),
                results.get("kline", []), results.get("news", []))
    stock_data, index_data, index_history, news_data = _load_extra()

# 持久化到数据库（去重逻辑在 db.py 内部）
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
        )

# 缓存数据供 AI 使用
st.session_state._funds_cache = all_funds_data
st.session_state._news_cache = news_data
st.session_state._index_cache = index_data

# AI 日报（页面首次加载时触发一次）
if "ai_report_generated" not in st.session_state and ai.api_key:
    st.session_state.ai_report_generated = False

if not st.session_state.ai_report_generated and ai.api_key:
    try:
        funds_data = []
        for code, fd in all_funds_data.items():
            funds_data.append({
                "code": code,
                "est": fd.get("estimate"),
                "hist": fd.get("history"),
                "holdings": fd.get("holdings"),
            })
        report = ai.daily_report(funds_data, index_data, news_data)
        st.session_state.ai_report = report
        st.session_state.ai_report_generated = True
        try:
            fund_codes = list(all_funds_data.keys())
            if report.get("risk"):
                save_ai_report("risk", report["risk"], fund_codes)
            if report.get("market"):
                save_ai_report("market", report["market"], fund_codes)
        except Exception as db_err:
            st.toast(f"AI 报告保存失败: {db_err}", icon="⚠️")
    except Exception as e:
        st.session_state.ai_report = {"risk": f"[分析失败: {e}]", "market": ""}
        st.session_state.ai_report_generated = True

ai_analysis = st.session_state.get("ai_report")

# ============================================
# 页面路由
# ============================================

page_key = page.replace("📡 ", "").replace("📊 ", "").replace("⚖️ ", "").replace("🎯 ", "")
page_key = page_key.replace("盯盘", "watch").replace("复盘", "review").replace("对比", "compare").replace("推荐", "recommend")

if page_key == "watch":
    default_fund = funds[0]["code"]
    fd = all_funds_data.get(default_fund)
    if fd:
        render_watch_page(fd, stock_data, index_data, news_data, ai_analysis)

elif page_key == "review":
    default_fund = funds[0]["code"]
    fd = all_funds_data.get(default_fund)
    ai_summary = None
    if fd:
        try:
            if ai.api_key and fd.get("estimate"):
                ai_summary = ai.daily_summary(
                    {"name": fd.get("name"), "change_pct": fd["estimate"]["estimate_change_pct"],
                     "estimate_change_pct": fd["estimate"]["estimate_change_pct"]},
                    stock_data, len(news_data)
                )
        except Exception:
            pass
        render_review_page(fd, stock_data, index_data, ai_summary)

elif page_key == "compare":
    render_compare_page(all_funds_data, index_history)

elif page_key == "recommend":
    render_recommend_page(ai)

# 自动刷新（不阻塞线程）
refresh_gap = config.get("refresh_interval_seconds", 120)
if "refresh_ts" not in st.session_state:
    st.session_state.refresh_ts = time.time()
elif time.time() - st.session_state.refresh_ts >= refresh_gap:
    st.session_state.refresh_ts = time.time()
    st.cache_data.clear()

# 页脚
st.markdown("""
<div style="margin-top:20px;font-size:11px;color:#3a3d4a;text-align:center">
数据来源: 天天基金 / 腾讯证券 / 新浪财经 | 自动刷新 120s | 投资有风险
</div>""", unsafe_allow_html=True)
