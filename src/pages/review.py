import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def render_review_page(fund_data, stock_data, index_data, ai_analysis):
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
        <div style="font-size:28px;font-weight:700;color:#e6e9f0">复盘</div>
        <div style="font-size:12px;color:#5a5d6a;background:#1a1d29;padding:4px 10px;border-radius:6px">盘后分析</div>
    </div>""", unsafe_allow_html=True)

    if not fund_data.get("history"):
        st.info("暂无历史数据")
        return

    df = pd.DataFrame(fund_data["history"])
    df["net_value"] = pd.to_numeric(df["net_value"], errors="coerce")
    daily_col = "daily_change_pct"
    if df[daily_col].dtype == object:
        df[daily_col] = pd.to_numeric(
            df[daily_col].apply(lambda x: x.replace("%", "") if isinstance(x, str) else x),
            errors="coerce",
        )
    else:
        df[daily_col] = pd.to_numeric(df[daily_col], errors="coerce")

    # 统计指标
    total_5d = df[daily_col].tail(5).sum()
    total_20d = df[daily_col].tail(20).sum() if len(df) >= 20 else None
    peak = df["net_value"].expanding().max()
    dd_series = ((df["net_value"] - peak) / peak * 100)
    max_dd = dd_series.min()
    win_rate = (df[daily_col] > 0).sum() / len(df) * 100

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:10px;padding:14px">
            <div style="font-size:12px;color:#8892b0">近5日</div>
            <div style="font-size:24px;font-weight:600;color:{'#00c853' if total_5d>=0 else '#ff1744'}">{total_5d:+.2f}%</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        val = f"{total_20d:+.2f}%" if total_20d is not None else "N/A"
        c = "#00c853" if (total_20d or 0) >= 0 else "#ff1744"
        st.markdown(f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:10px;padding:14px">
            <div style="font-size:12px;color:#8892b0">近20日</div>
            <div style="font-size:24px;font-weight:600;color:{c}">{val}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:10px;padding:14px">
            <div style="font-size:12px;color:#8892b0">最大回撤</div>
            <div style="font-size:24px;font-weight:600;color:#ff1744">{max_dd:.2f}%</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:10px;padding:14px">
            <div style="font-size:12px;color:#8892b0">胜率</div>
            <div style="font-size:24px;font-weight:600;color:#64b5f6">{win_rate:.1f}%</div>
        </div>""", unsafe_allow_html=True)

    # 图表：净值曲线 + 回撤趋势 + 日涨跌幅
    st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📈 净值曲线", "📉 回撤趋势", "📊 日涨跌幅"])

    with tab1:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=df["date"], y=df["net_value"],
            mode="lines", name="净值",
            line=dict(color="#64b5f6", width=2),
            fill="tozeroy", fillcolor="rgba(100,181,246,0.06)",
        ))
        fig1.update_layout(
            height=350, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(color="#8892b0", size=11),
            xaxis=dict(showgrid=False, linecolor="#2a2d3a"),
            yaxis=dict(showgrid=True, gridcolor="#1a1d29", linecolor="#2a2d3a"),
        )
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

    with tab2:
        # 回撤趋势图（新增功能）
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=df["date"], y=dd_series,
            mode="lines", name="回撤",
            line=dict(color="#ff1744", width=2),
            fill="tozeroy", fillcolor="rgba(255,23,68,0.06)",
        ))
        # 标注 -5% 警戒线
        fig_dd.add_hline(y=-5, line_dash="dash", line_color="#ff9800", annotation_text="警戒线 -5%",
                         annotation_font=dict(color="#ff9800", size=10))
        fig_dd.add_hline(y=-10, line_dash="dash", line_color="#d32f2f", annotation_text="止损线 -10%",
                         annotation_font=dict(color="#d32f2f", size=10))
        fig_dd.update_layout(
            height=350, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(color="#8892b0", size=11),
            xaxis=dict(showgrid=False, linecolor="#2a2d3a"),
            yaxis=dict(showgrid=True, gridcolor="#1a1d29", linecolor="#2a2d3a"),
        )
        st.plotly_chart(fig_dd, use_container_width=True, config={"displayModeBar": False})
        st.caption("回撤 = (当前净值 - 区间最高净值) / 区间最高净值 × 100%")

    with tab3:
        recent = df.tail(10)
        colors = ["#00c853" if c >= 0 else "#ff1744" for c in recent[daily_col]]
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=recent["date"], y=recent[daily_col],
            marker_color=colors, name="日涨跌幅",
            text=recent[daily_col].apply(lambda x: f"{x:+.2f}%"),
            textposition="outside", textfont=dict(size=10),
        ))
        fig2.update_layout(
            height=350, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(color="#8892b0", size=10),
            xaxis=dict(showgrid=False, linecolor="#2a2d3a"),
            yaxis=dict(showgrid=True, gridcolor="#1a1d29", linecolor="#2a2d3a"),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # AI 研判
    if ai_analysis:
        st.markdown("<div style='font-size:15px;font-weight:600;color:#e6e9f0;margin:12px 0 6px'>AI 今日研判</div>", unsafe_allow_html=True)
        st.markdown(
            f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:8px;padding:12px;font-size:13px;color:#c5c8d4;line-height:1.5">{ai_analysis}</div>""",
            unsafe_allow_html=True)

    # 重仓股表现
    if stock_data:
        st.markdown("<div style='font-size:15px;font-weight:600;color:#e6e9f0;margin:16px 0 8px'>重仓股表现</div>", unsafe_allow_html=True)
        rows = []
        for s in stock_data:
            if "error" not in s:
                rows.append({"名称": s["name"], "现价": s["price"], "涨跌幅": s["change_pct"]})
        if rows:
            df_stock = pd.DataFrame(rows)
            fig3 = go.Figure()
            for _, r in df_stock.iterrows():
                color = "#00c853" if r["涨跌幅"] >= 0 else "#ff1744"
                fig3.add_trace(go.Bar(
                    x=[r["名称"]], y=[r["涨跌幅"]],
                    marker_color=color, name=r["名称"],
                    text=f"{r['涨跌幅']:+.2f}%", textposition="outside",
                    textfont=dict(size=10), width=0.6,
                ))
            fig3.update_layout(
                height=250, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(color="#8892b0", size=11),
                xaxis=dict(showgrid=False, linecolor="#2a2d3a"),
                yaxis=dict(showgrid=True, gridcolor="#1a1d29", linecolor="#2a2d3a"),
                barmode="group", showlegend=False,
            )
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='margin-top:16px;font-size:11px;color:#3a3d4a;text-align:center'>数据来源: 天天基金 / 腾讯证券</div>", unsafe_allow_html=True)
