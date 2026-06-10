# test_minimal.py - 最小化测试看板
import streamlit as st
import sys, os
sys.path.insert(0, 'D:/fund_monitor')

from src.data.fund import get_realtime_estimate

st.set_page_config(page_title='Test', layout='wide')

st.title('Test Dashboard')

with st.spinner('Loading...'):
    est = get_realtime_estimate('110011')

if est:
    st.metric(est['name'], f'{est["estimate_value"]:.4f}', f'{est["estimate_change_pct"]:+.2f}%')
else:
    st.error('Failed to load data')

st.success('Dashboard is working!')
