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
    for fund_code, fund_data in all_funds_data.items():
        if fund_data.get("history"):
            df = pd.DataFrame(fund_data["history"])
            df["net_value"] = pd.to_numeric(df["net_value"], errors="coerce")
            name = fund_data.get("name", fund_code)[:10]
            fig.add_trace(go.Scatter(
                x=df["date"], y=df["net_value"],
                mode="lines", name=name,
                line=dict(width=1.5),
            ))

    if index_history:
        df_idx = pd.DataFrame(index_history)
        if not df_idx.empty:
            fig.add_trace(go.Scatter(
                x=df_idx["date"], y=df_idx["close"],
                mode="lines", name="沪深300",
                line=dict(color="rgba(255,183,77,0.7)", width=1.5, dash="dash"),
            ))

    fig.update_layout(
        height=250, margin=dict(l=0, r=0, t=5, b=0),
        paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
        font=dict(color="#8892b0", size=9),
        xaxis=dict(showgrid=False, linecolor="#2a2d3a", tickangle=-45),
        yaxis=dict(showgrid=True, gridcolor="#1a1d29", linecolor="#2a2d3a"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=8)),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # 指标对比表
    rows = []
    for fund_code, fund_data in all_funds_data.items():
        if fund_data.get("history"):
            df = pd.DataFrame(fund_data["history"])
            daily_chg = pd.to_numeric(
                df["daily_change_pct"].apply(
                    lambda x: x.replace("%", "") if isinstance(x, str) else x
                ), errors="coerce"
            )
            metrics = _calc_metrics(daily_chg)
            row = {"基金": fund_data.get("name", fund_code)[:12]}
            row["近5日"] = f"{daily_chg.tail(5).sum():+.1f}%" if len(daily_chg) >= 5 else "N/A"
            row["夏普"] = metrics.get("夏普比率", "N/A")
            row["波动"] = metrics.get("年化波动率", "N/A")
            row["回撤"] = metrics.get("最大回撤", "N/A")
            rows.append(row)

    if index_history:
        df_idx = pd.DataFrame(index_history)
        daily_idx = []
        for i in range(1, len(df_idx)):
            if df_idx.iloc[i]["close"] and df_idx.iloc[i-1]["close"]:
                chg = (df_idx.iloc[i]["close"] - df_idx.iloc[i-1]["close"]) / df_idx.iloc[i-1]["close"] * 100
                daily_idx.append(chg)
        if daily_idx:
            da = pd.Series(daily_idx)
            idx_metrics = _calc_metrics(da)
            row = {"基金": "沪深300"}
            row["近5日"] = f"{da.tail(5).sum():+.1f}%" if len(da) >= 5 else "N/A"
            row["夏普"] = idx_metrics.get("夏普比率", "N/A")
            row["波动"] = idx_metrics.get("年化波动率", "N/A")
            row["回撤"] = idx_metrics.get("最大回撤", "N/A")
            rows.append(row)

    if rows:
        df_table = pd.DataFrame(rows)
        styled = df_table.style.applymap(
            lambda v: "color:#00c853" if isinstance(v, str) and v.startswith("+") else (
                     "color:#ff1744" if isinstance(v, str) and v.startswith("-") else ""),
            subset=["近5日"]
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

    # 夏普比率横向条形图
    if rows:
        sharpes = [(r["基金"], r["夏普"]) for r in rows if r.get("夏普") and r["夏普"] != "N/A"]
        if sharpes:
            fig_s = go.Figure()
            for name, sv_str in sharpes:
                try:
                    sv = float(sv_str)
                    color = "#00c853" if sv > 0.5 else ("#ff9800" if sv > 0 else "#ff1744")
                    fig_s.add_trace(go.Bar(
                        x=[name], y=[sv],
                        marker_color=color,
                        text=f"{sv:.2f}", textposition="outside",
                        textfont=dict(size=8),
                        width=0.4,
                    ))
                except:
                    pass
            fig_s.update_layout(
                height=180, margin=dict(l=0, r=0, t=5, b=0),
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(color="#8892b0", size=8),
                xaxis=dict(showgrid=False, linecolor="#2a2d3a"),
                yaxis=dict(showgrid=True, gridcolor="#1a1d29", linecolor="#2a2d3a", title="夏普"),
                showlegend=False,
            )
            st.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar": False})
