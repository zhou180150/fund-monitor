# app_simple.py - ????
import streamlit as st
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.data.fund import get_realtime_estimate, get_holdings
from src.data.stock import get_stock_realtime, get_index_realtime

st.set_page_config(page_title='????', layout='wide')
st.title('??????')

with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf-8') as f:
    config = json.load(f)

funds = config.get('funds', [])
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader('????')
    for f in funds:
        est = get_realtime_estimate(f['code'])
        if est and 'error' not in est:
            st.metric(f['name'], f'{est["estimate_value"]:.4f}',
                     f'{est["estimate_change_pct"]:+.2f}%')

with col2:
    st.subheader('???')
    for f in funds[:1]:
        h = get_holdings(f['code'])
        names = [x['name'] for x in h[:4]]
        st.write(' | '.join(names))

with col3:
    st.subheader('??')
    idx = get_index_realtime('sh000300')
    if idx and 'error' not in idx[0]:
        st.metric(idx[0]['name'], f'{idx[0]["price"]}',
                 f'{idx[0]["change_pct"]:+.2f}%')

st.success('??????')
