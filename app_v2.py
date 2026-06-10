# app_v2.py - 基金监控看板入口（完整版）
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

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.fund import get_realtime_estimate, get_net_value_history, get_holdings
from src.data.stock import get_stock_realtime, get_index_realtime, get_stock_kline
from src.data.news import fetch_market_news, filter_news_by_keywords
from src.analysis.indicators import calc_ma, calc_max_drawdown, calc_win_rate, calc_volatility
from src.analysis.advisor import AIAdvisor
from src.pages.watch import render_watch_page
from src.pages.review import render_review_page
from src.pages.compare import render_compare_page
from src.pages.recommend import render_recommend_page

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
</style>
"""

st.set_page_config(
    page_title="基金监控看板",
    page_icon="",
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

# DeepSeek 初始化
ai = AIAdvisor(os.getenv("DEEPSEEK_API_KEY", config.get("deepseek_api_key", "")))

# ============================================
# 数据加载函数（缓存 120 秒）
# ============================================

@st.cache_data(ttl=120, show_spinner=False)
def load_fund_data(fund_code):
    """加载单只基金的全量数据"""
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
    """加载所有股票行情"""
    if not all_codes:
        return []
    return get_stock_realtime(list(set(all_codes)))

@st.cache_data(ttl=120, show_spinner=False)
def load_index_data():
    """加载指数行情"""
    return get_index_realtime(benchmark)

@st.cache_data(ttl=120, show_spinner=False)
def load_index_history():
    """加载指数历史K线"""
    return get_stock_kline("sh000300", 60)

@st.cache_data(ttl=300, show_spinner=False)
def load_news_data(keywords=None):
    """加载并过滤新闻"""
    news = fetch_market_news()
    if keywords:
        news = filter_news_by_keywords(news, keywords)
    return news

# ============================================
# 侧边栏：导航 + 配置
# ============================================

st.sidebar.title("基金监控")
st.sidebar.caption(f"交易日 {date.today()}")

# 导航
page = st.sidebar.radio("导航", ["盯盘", "复盘", "对比", "推荐"], horizontal=True)

# 刷新按钮
if st.sidebar.button("刷新数据", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
    time.sleep(0.5)

st.sidebar.divider()
st.sidebar.caption("当前关注基金:")
for f in funds:
    st.sidebar.text(f["name"])
st.sidebar.caption(f"自动刷新间隔: {config.get('refresh_interval_seconds', 120)}秒")
st.sidebar.caption("数据来源: 天天基金 / 腾讯证券 / 新浪财经")

st.sidebar.divider()
st.sidebar.markdown("<div style='font-size:14px;font-weight:600;color:#64b5f6;margin:4px 0'>AI 管家</div>",
                    unsafe_allow_html=True)

# 对话历史
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "我是 AI 基金管家，随时为你分析持仓、市场或推荐基金。"}
    ]

# 聊天显示区（固定高度滚动）
with st.sidebar.expander("聊天记录", expanded=True):
    for msg in st.session_state.chat_history[-8:]:
        if msg["role"] == "assistant":
            st.markdown(
                f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:10px;padding:10px;margin-bottom:6px;font-size:12px;line-height:1.5;color:#c5c8d4">{msg["content"][:200]}</div>""",
                unsafe_allow_html=True)
        else:
            st.markdown(
                f"""<div style="text-align:right;padding:6px 10px;margin-bottom:4px;font-size:12px;color:#8892b0">你：{msg["content"][:80]}</div>""",
                unsafe_allow_html=True)

# 快捷问题按钮
quick_qs = ["我的基金风险如何", "今天市场怎么样", "这个位置该不该加仓"]
cols = st.sidebar.columns(3)
for i, q in enumerate(quick_qs):
    with cols[i]:
        if st.button(q[:4], key=f"qq_{i}"):
            if "all_funds_data" in dir() or "all_funds_data" in locals():
                pass

# 输入框
user_input = st.sidebar.chat_input("问我任何基金问题...")
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    with st.spinner("AI 思考中..."):
        try:
            import json
            
            fund_names = ""
            fd_list = []
            if "all_funds_data" in st.session_state:
                for code, fd in st.session_state.get("_funds_data", {}).items():
                    nm = fd.get("name", code)
                    fund_names += f"- {nm}\n"
                    fd_list.append(fd)
            
            context = f"用户当前持仓基金：\n{fund_names}\n用户问题：{user_input}\n\n请用中文回答，300字以内。"
            resp = ai.call_api("你是一个专业的中国基金分析管家，回答要简洁、有依据。", context, max_tokens=500)
            st.session_state.chat_history.append({"role": "assistant", "content": resp})
            try:
                from src.data.db import save_chat
                save_chat(user_input, resp)
            except Exception:
                pass
        except Exception as e:
            st.session_state.chat_history.append({"role": "assistant", "content": f"[分析失败: {e}]"})
            try:
                from src.data.db import save_chat
                save_chat(user_input, f"[分析失败: {e}]")
            except Exception:
                pass
    st.rerun()

st.sidebar.caption("Powered by DeepSeek")
# ============================================
# 数据加载
# ============================================

if not funds:
    st.error("请在 config.json 中添加关注的基金代码")
    st.stop()

# 并行加载所有基金数据
all_funds_data = {}
all_stock_codes = []
news_keywords = ["基金", "A股", "市场", "股市", "行情", "投资"]

with st.spinner("加载数据中..."):
    # 多线程并行加载所有基金的数据
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
            results['stocks'] = load_all_stock_data(codes) if codes else []
        def _get_index():
            results['idx'] = load_index_data()
        def _get_kline():
            results['kline'] = load_index_history()
        def _get_news():
            results['news'] = load_news_data(keywords=news_keywords)
        threads = [
            threading.Thread(target=_get_stocks, daemon=True),
            threading.Thread(target=_get_index, daemon=True),
            threading.Thread(target=_get_kline, daemon=True),
            threading.Thread(target=_get_news, daemon=True),
        ]
        for t in threads: t.start()
        for t in threads: t.join(timeout=15)
        return results.get('stocks', []), results.get('idx', []), results.get('kline', []), results.get('news', [])
    stock_data, index_data, index_history, news_data = _load_extra()

# ======== 持久化到数据库 ========
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
        )

# 缓存基金数据供 AI 管家使用
st.session_state._funds_cache = all_funds_data
st.session_state._news_cache = news_data
st.session_state._index_cache = index_data

# AI 分析：在数据加载完成后触发（由 session_state 控制）
ai_analysis = None
if "ai_loading" not in st.session_state:
    st.session_state.ai_loading = False
if st.session_state.get("ai_loading") and ai.api_key:
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
        st.session_state.ai_loading = False
        try:
            from src.data.db import save_ai_report
            fund_codes = list(all_funds_data.keys())
            save_ai_report("risk", report.get("risk", ""), fund_codes)
            if report.get("market"):
                save_ai_report("market", report.get("market", ""), fund_codes)
        except Exception:
            pass
    except Exception as e:
        st.session_state.ai_report = {"risk": f"[分析失败: {e}]", "market": ""}
        st.session_state.ai_loading = False

# ============================================
# 页面路由
# ============================================

if page == "盯盘":
    # 盯盘页面默认展示第一只基金
    default_fund = funds[0]["code"]
    fd = all_funds_data[default_fund]
    render_watch_page(fd, stock_data, index_data, news_data, ai_analysis)

elif page == "复盘":
    default_fund = funds[0]["code"]
    fd = all_funds_data[default_fund]
    ai_summary = None
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

elif page == "对比":
    render_compare_page(all_funds_data, index_history)

elif page == "推荐":
    render_recommend_page(ai)

# 自动刷新（间隔由 config.json 控制）
refresh_gap = config.get("refresh_interval_seconds", 120)
if "refresh_ts" not in st.session_state:
    st.session_state.refresh_ts = time.time()
elif time.time() - st.session_state.refresh_ts >= refresh_gap:
    st.session_state.refresh_ts = time.time()
    st.cache_data.clear()
    st.rerun()
    time.sleep(0.5)
