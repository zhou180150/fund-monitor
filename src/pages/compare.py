# compare.py - 对比页面（移动端优化）

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def _calc_metrics(daily_chg_series):
    chgs = daily_chg_series.dropna()
    if len(chgs) < 5:
        return {}
    vol = chgs.std() * np.sqrt(252)
    sharpe = (chgs.mean() / chgs.std() * np.sqrt(252)) if chgs.std() > 0 else 0
    cumulative = (1 + chgs / 100).cumprod()
    rolling_max = cumulative.expanding().max()
    dd = ((cumulative - rolling_max) / rolling_max * 100).min()
    wr = (chgs > 0).sum() / len(chgs) * 100
    return {
        "年化波动率": f"{vol:.1f}%",
        "夏普比率": f"{sharpe:.2f}",
        "最大回撤": f"{dd:.1f}%",
        "胜率": f"{wr:.0f}%",
    }

def render_compare_page(all_funds_data, index_history):
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <div style="font-size:20px;font-weight:700;color:#e6e9f0">对比</div>
        <div style="font-size:10px;color:#5a5d6a;background:#1a1d29;padding:2px 8px;border-radius:4px">多基金+基准</div>
    </div>""", unsafe_allow_html=True)

    if not all_funds_data:
        st.info("添加更多基金到 config.json 即可在此页面对比")
        return

    # 净值叠加图
    fig = go.Figure()
    # ??????????????=100???????????
    for fund_code, fund_data in all_funds_data.items():
        if fund_data.get("history"):
            df = pd.DataFrame(fund_data["history"])
            vals = pd.to_numeric(df["net_value"], errors="coerce").dropna().values
            if len(vals) > 0:
                base = vals[0]
                norm = (vals / base) * 100 if base > 0 else vals
                dates = df["date"].iloc[:len(norm)]
                name = fund_data.get("name", fund_code)[:10]
                fig.add_trace(go.Scatter(x=dates, y=norm, mode="lines", name=name, line=dict(width=1.5),
                    hovertemplate="%s%%{y:.1f} (base=100)" % name))
    if index_history:
        df_idx = pd.DataFrame(index_history)
        close_vals = pd.to_numeric(df_idx["close"], errors="coerce").dropna().values
        if len(close_vals) > 0:
            base_idx = close_vals[0]
            norm_idx = (close_vals / base_idx) * 100 if base_idx > 0 else close_vals
            dates_idx = df_idx["date"].iloc[:len(norm_idx)]
            fig.add_trace(go.Scatter(x=dates_idx, y=norm_idx, mode="lines", name="\u6caa\u6df1300",
                line=dict(color="rgba(255,183,77,0.7)", width=1.5, dash="dash"),
                hovertemplate="%s%%{y:.1f} (base=100)" % "\u6caa\u6df1300"))
    fig.update_layout(height=250, margin=dict(l=0, r=0, t=5, b=0), paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
        font=dict(color="#8892b0", size=9),
        xaxis=dict(showgrid=False, linecolor="#2a2d3a", tickangle=-45),
        yaxis=dict(showgrid=True, gridcolor="#1a1d29", linecolor="#2a2d3a",
            ticksuffix="%", title="\u76f8\u5bf9\u6536\u76ca\u7387 (base=100)"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=8)))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

