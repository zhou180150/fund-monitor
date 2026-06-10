# app.py - 基金监控看板入口
# 运行: streamlit run app.py

import streamlit as st
import json
import os
import sys
import time
from datetime import datetime, date

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.fund import get_realtime_estimate, get_net_value_history, get_holdings
from src.data.stock import get_stock_realtime, get_index_realtime, get_stock_kline
from src.data.news import fetch_market_news, filter_news_by_keywords
from src.analysis.indicators import calc_ma, calc_max_drawdown, calc_win_rate, calc_volatility
from src.analysis.deepseek import DeepSeekAnalyzer
from src.pages.watch import render_watch_page
from src.pages.review import render_review_page
from src.pages.compare import render_compare_page

# 页面配置
st.set_page_config(
    page_title="基金监控看板",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
ai = DeepSeekAnalyzer(config.get("deepseek_api_key", ""))

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
    return get_stock_kline("000300", 60)

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

st.sidebar.title("  基金监控")
st.sidebar.caption(f"交易日 {date.today()}")

# 导航
page = st.sidebar.radio("导航", ["盯盘", "复盘", "对比"], horizontal=True)

# 刷新按钮
if st.sidebar.button("  刷新数据", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.caption("当前关注基金:")
for f in funds:
    st.sidebar.text(f["name"])
st.sidebar.caption(f"自动刷新间隔: {config.get('refresh_interval_seconds', 120)}秒")
st.sidebar.caption("数据来源: 天天基金 / 腾讯证券 / 新浪财经")

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
    for f in funds:
        fund_data = load_fund_data(f["code"])
        all_funds_data[f["code"]] = fund_data
        # 收集所有持仓股票代码
        if fund_data.get("holdings"):
            for h in fund_data["holdings"]:
                all_stock_codes.append(h["code"])

    # 加载行情 & 新闻
    stock_data = load_all_stock_data(all_stock_codes) if all_stock_codes else []
    index_data = load_index_data()
    index_history = load_index_history()
    news_data = load_news_data(keywords=news_keywords)

# AI 分析（仅在交易时段或新闻变化时）
ai_analysis = None
if ai.api_key and news_data:
    first_fund_name = all_funds_data[funds[0]["code"]].get("name", "")
    ai_analysis = ai.analyze_news(news_data, first_fund_name)

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

# 自动刷新
time.sleep(0.5)
st.rerun()
