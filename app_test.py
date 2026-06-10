# app_test.py - 端到端测试版
import streamlit as st
import sys, os, json
sys.path.insert(0, 'D:/fund_monitor')

from src.data.fund import get_realtime_estimate, get_net_value_history, get_holdings
from src.data.stock import get_stock_realtime, get_index_realtime, get_stock_kline
from src.data.news import fetch_market_news, filter_news_by_keywords
from src.analysis.indicators import calc_ma, calc_max_drawdown, calc_win_rate, calc_volatility
from src.analysis.deepseek import DeepSeekAnalyzer

st.set_page_config(page_title='基金测试', layout='wide', initial_sidebar_state='expanded')

# 加载配置
with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf-8') as f:
    config = json.load(f)

funds = config.get('funds', [])

st.sidebar.title('基金测试')
page = st.sidebar.radio('页面', ['盯盘', '复盘', '对比', '数据测试'])

if page == '数据测试':
    st.title('数据接口测试')
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('基金接口')
        for f in funds[:1]:
            est = get_realtime_estimate(f['code'])
            if est and 'error' not in est:
                st.metric(f['name'], f'{est["estimate_value"]:.4f}', f'{est["estimate_change_pct"]:+.2f}%')
            holdings = get_holdings(f['code'])
            if holdings:
                st.write(f'持仓: {len(holdings)}只')
                st.dataframe(holdings[:5])
        
        st.subheader('股票接口')
        stocks = get_stock_realtime(['600519', '000858', '600809'])
        for s in stocks:
            if 'error' not in s:
                st.write(f'{s["name"]}: {s["price"]} ({s["change_pct"]}%)')
    
    with col2:
        st.subheader('指数')
        idx = get_index_realtime('sh000300')
        if idx and 'error' not in idx[0]:
            st.metric(f'{idx[0]["name"]}', f'{idx[0]["price"]}', f'{idx[0]["change_pct"]:+.2f}%')
        
        st.subheader('新闻')
        news = fetch_market_news()
        st.write(f'共{len(news)}条')
        for n in news[:5]:
            st.caption(f'{n["title"][:40]}')
        
        st.subheader('技术指标')
        hist = get_net_value_history('110011', per_page=30)
        prices = [h['net_value'] for h in hist if h['net_value']]
        if prices:
            st.metric('最大回撤', f'{calc_max_drawdown(prices):.2f}%')
            st.metric('胜率', f'{calc_win_rate(prices):.1f}%')
    
    st.success('所有接口测试完成')

else:
    st.info(f'{page}页面 - 简化版测试中')
    st.metric('基金数', len(funds))
    for f in funds:
        est = get_realtime_estimate(f['code'])
        if est:
            st.write(f'{f["name"]}: {est["estimate_value"]:.4f} ({est["estimate_change_pct"]:+.2f}%)')
