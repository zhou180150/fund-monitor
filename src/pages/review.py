# review.py - 复盘页面（移动端优化）

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def render_review_page(fund_data, stock_data, index_data, ai_analysis):
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <div style="font-size:20px;font-weight:700;color:#e6e9f0">复盘</div>
        <div style="font-size:10px;color:#5a5d6a;background:#1a1d29;padding:2px 8px;border-radius:4px">盘后分析</div>
    </div>""", unsafe_allow_html=True)

    if not fund_data.get("history"):
        st.info("暂无历史数据")
        return

    df = pd.DataFrame(fund_data["history"])
    df["net_value"] = pd.to_numeric(df["net_value"], errors="coerce")
    daily_col = "daily_change_pct"
    df[daily_col] = pd.to_numeric(df[daily_col].apply(lambda x: str(x).replace("%", "")), errors="coerce")

    # 指标
    total_5d = df[daily_col].tail(5).sum()
    total_20d = df[daily_col].tail(20).sum() if len(df) >= 20 else None
    peak = df["net_value"].expanding().max()
    dd_series = ((df["net_value"] - peak) / peak * 100)
    max_dd = dd_series.min()
    win_rate = (df[daily_col] > 0).sum() / len(df) * 100

    # 四指标 2x2 网格
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:8px;padding:10px;margin-bottom:6px">
            <div style="font-size:10px;color:#8892b0">近5日</div>
            <div style="font-size:18px;font-weight:600;color:{'#00c853' if total_5d>=0 else '#ff1744'}">{total_5d:+.2f}%</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        val = f"{total_20d:+.2f}%" if total_20d is not None else "N/A"
        c = "#00c853" if (total_20d or 0) >= 0 else "#ff1744"
        st.markdown(f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:8px;padding:10px;margin-bottom:6px">
            <div style="font-size:10px;color:#8892b0">近20日</div>
            <div style="font-size:18px;font-weight:600;color:{c}">{val}</div>
        </div>""", unsafe_allow_html=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown(f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:8px;padding:10px;margin-bottom:6px">
            <div style="font-size:10px;color:#8892b0">最大回撤</div>
            <div style="font-size:18px;font-weight:600;color:#ff1744">{max_dd:.2f}%</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:8px;padding:10px;margin-bottom:6px">
            <div style="font-size:10px;color:#8892b0">胜率</div>
            <div style="font-size:18px;font-weight:600;color:#64b5f6">{win_rate:.1f}%</div>
        </div>""", unsafe_allow_html=True)

    # 图表（三个 tab，移动端友好高度）
    tab1, tab2, tab3 = st.tabs(["净值", "回撤", "日涨跌"])

    with tab1:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=df["date"], y=df["net_value"],
            mode="lines", name="净值",
            line=dict(color="#64b5f6", width=1.5),
            fill="tozeroy", fillcolor="rgba(100,181,246,0.06)",
        ))
        fig1.update_layout(
            height=200, margin=dict(l=0, r=0, t=5, b=0),
            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(color="#8892b0", size=9),
            xaxis=dict(showgrid=False, linecolor="#2a2d3a", tickangle=-45),
            yaxis=dict(showgrid=True, gridcolor="#1a1d29", linecolor="#2a2d3a"),
        )
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

    with tab2:
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=df["date"], y=dd_series,
            mode="lines", name="回撤",
            line=dict(color="#ff1744", width=1.5),
            fill="tozeroy", fillcolor="rgba(255,23,68,0.06)",
        ))
        fig_dd.add_hline(y=-5, line_dash="dash", line_color="#ff9800", annotation_text="-5%",
                         annotation_font=dict(color="#ff9800", size=8))
        fig_dd.add_hline(y=-10, line_dash="dash", line_color="#d32f2f", annotation_text="-10%",
                         annotation_font=dict(color="#d32f2f", size=8))
        fig_dd.update_layout(
            height=200, margin=dict(l=0, r=0, t=5, b=0),
            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(color="#8892b0", size=9),
            xaxis=dict(showgrid=False, linecolor="#2a2d3a", tickangle=-45),
            yaxis=dict(showgrid=True, gridcolor="#1a1d29", linecolor="#2a2d3a"),
        )
        st.plotly_chart(fig_dd, use_container_width=True, config={"displayModeBar": False})
        st.caption("回撤 = (净值 - 最高) / 最高 × 100%")

    with tab3:
        recent = df.tail(10)
        colors = ["#00c853" if c >= 0 else "#ff1744" for c in recent[daily_col]]
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=recent["date"], y=recent[daily_col],
            marker_color=colors, name="日涨跌幅",
            text=recent[daily_col].apply(lambda x: f"{x:+.1f}%"),
            textposition="outside", textfont=dict(size=8),
        ))
        fig2.update_layout(
            height=200, margin=dict(l=0, r=0, t=5, b=0),
            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(color="#8892b0", size=8),
            xaxis=dict(showgrid=False, linecolor="#2a2d3a", tickangle=-45),
            yaxis=dict(showgrid=True, gridcolor="#1a1d29", linecolor="#2a2d3a"),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # AI 研判（若存在）
    if ai_analysis:
        st.markdown("<div style='font-size:12px;font-weight:600;color:#64b5f6;margin:8px 0 4px'>AI 今日研判</div>", unsafe_allow_html=True)
        st.markdown(
            f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:6px;padding:8px;font-size:11px;color:#c5c8d4;line-height:1.4">{ai_analysis[:250]}</div>""",
            unsafe_allow_html=True)

    # 重仓股表现（紧凑水平条形图）
    if stock_data:
        rows = []
        for s in stock_data:
            if "error" not in s:
                rows.append({"名称": s["name"], "涨跌幅": s["change_pct"]})
        if rows:
            st.markdown("<div style='font-size:13px;font-weight:600;color:#e6e9f0;margin:10px 0 4px'>重仓股表现</div>", unsafe_allow_html=True)
            df_stock = pd.DataFrame(rows)
            fig3 = go.Figure()
            for _, r in df_stock.iterrows():
                color = "#00c853" if r["涨跌幅"] >= 0 else "#ff1744"
                fig3.add_trace(go.Bar(
                    x=[r["名称"]], y=[r["涨跌幅"]],
                    marker_color=color, name=r["名称"],
                    text=f"{r['涨跌幅']:+.1f}%", textposition="outside",
                    textfont=dict(size=8), width=0.5,
                ))
            fig3.update_layout(
                height=180, margin=dict(l=0, r=0, t=5, b=0),
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(color="#8892b0", size=9),
                xaxis=dict(showgrid=False, linecolor="#2a2d3a"),
                yaxis=dict(showgrid=True, gridcolor="#1a1d29", linecolor="#2a2d3a"),
                barmode="group", showlegend=False,
            )
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

