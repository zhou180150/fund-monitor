# watch.py - 盯盘页面（重写UI）

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime


# -------- CSS 卡片组件 --------
def _card(title, value, subtitle, color=None, extra=None):
    """统一的指标卡片"""
    val_color = f"color:{color};" if color else ""
    extra_html = f"<div style='font-size:12px;color:#8892b0;margin-top:4px'>{extra}</div>" if extra else ""
    return f"""
    <div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:12px;padding:16px;margin-bottom:10px">
        <div style="font-size:13px;color:#8892b0;margin-bottom:6px">{title}</div>
        <div style="font-size:28px;font-weight:600;{val_color}">{value}</div>
        <div style="font-size:13px;color:#5a5d6a">{subtitle}</div>
        {extra_html}
    </div>"""


def render_watch_page(fund_data, stock_data, index_data, news_data, ai_analysis):
    # 页面标题
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
        <div style="font-size:28px;font-weight:700;color:#e6e9f0">盯盘</div>
        <div style="font-size:12px;color:#5a5d6a;background:#1a1d29;padding:4px 10px;border-radius:6px">
            """ + (f"{datetime.now().strftime('%H:%M')}" ) + """ 更新
        </div>
    </div>""", unsafe_allow_html=True)

    # ======== 第一行：关键指标卡片 ========
    est = fund_data.get("estimate")

    cards = []
    # 基金涨幅卡片
    if est and "error" not in est:
        chg = est["estimate_change_pct"]
        c = "#00c853" if chg >= 0 else "#ff1744"
        arrow = "▲" if chg >= 0 else "▼"
        cards.append((
            est.get("name", "基金"),
            f"{arrow} {chg:+.2f}%",
            f"估值 {est['estimate_value']:.4f} | 净值 {est['net_value']:.4f}",
            c,
            est.get("estimate_time", ""),
        ))
    else:
        cards.append(("基金", "N/A", "非交易时段", "#5a5d6a", ""))

    # 沪深300卡片
    if index_data:
        idx = index_data[0] if isinstance(index_data, list) else index_data
        if "error" not in idx:
            c = "#00c853" if idx["change_pct"] >= 0 else "#ff1744"
            arrow = "▲" if idx["change_pct"] >= 0 else "▼"
            cards.append((
                idx.get("name", "沪深300"),
                f"{arrow} {idx['change_pct']:+.2f}%",
                f"{idx.get('price', '')}",
                c,
            ))

    # 新闻数 / 持仓数
    stock_count = len([s for s in (stock_data or []) if "error" not in s])
    news_count = len(news_data or [])
    cards.append(("监控概览", f"{stock_count} 只股票", f"{news_count} 条新闻", "#64b5f6", ""))
    cards.append(("更新时间", datetime.now().strftime("%H:%M:%S"), "自动刷新 120s", "#8892b0", ""))

    cols = st.columns(len(cards))
    for i, (title, val, sub, color, *extra) in enumerate(cards):
        with cols[i]:
            st.markdown(_card(title, val, sub, color, extra[0] if extra else None), unsafe_allow_html=True)

    # ======== 第二行：双列布局 ========
    col1, col2 = st.columns([1.2, 1])

    with col1:
        # 净值走势图
        if fund_data.get("history"):
            st.markdown("<div style='font-size:15px;font-weight:600;color:#e6e9f0;margin-bottom:8px'>净值走势</div>",
                        unsafe_allow_html=True)
            df = pd.DataFrame(fund_data["history"])
            df["net_value"] = pd.to_numeric(df["net_value"], errors="coerce")
            fig = px.line(df, x="date", y="net_value")
            fig.update_layout(
                height=300, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(color="#8892b0", size=11),
                xaxis=dict(showgrid=False, linecolor="#2a2d3a"),
                yaxis=dict(showgrid=True, gridcolor="#1a1d29", linecolor="#2a2d3a"),
            )
            fig.update_traces(line=dict(color="#64b5f6", width=2))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # 持仓详情
        if stock_data:
            st.markdown("<div style='font-size:15px;font-weight:600;color:#e6e9f0;margin:12px 0 8px'>重仓股实时</div>",
                        unsafe_allow_html=True)
            rows = []
            for s in stock_data:
                if "error" not in s:
                    chg = s.get("change_pct", 0)
                    arrow = "▲" if chg >= 0 else "▼"
                    c = "#00c853" if chg >= 0 else "#ff1744"
                    rows.append({
                        "股票": s.get("name", ""),
                        "现价": s.get("price", ""),
                        " ": f"{arrow} {chg:+.2f}%",
                    })
            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True,
                             column_config={
                                 "股票": st.column_config.TextColumn(width="medium"),
                                 "现价": st.column_config.TextColumn(width="small"),
                                 " ": st.column_config.TextColumn(width="medium"),
                             })
            else:
                st.caption("暂无重仓股实时行情")

    with col2:
        # 大盘指数
        if index_data:
            idx = index_data[0] if isinstance(index_data, list) else index_data
            if "error" not in idx:
                c = "#00c853" if idx["change_pct"] >= 0 else "#ff1744"
                arrow = "▲" if idx["change_pct"] >= 0 else "▼"
                st.markdown(
                    f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:10px;padding:14px">
                        <div style="display:flex;justify-content:space-between">
                            <span style="color:#8892b0">{idx.get("name", "沪深300")}</span>
                            <span style="color:{c};font-weight:600">{arrow} {idx["change_pct"]:+.2f}%</span>
                        </div>
                        <div style="font-size:22px;font-weight:600;color:#e6e9f0;margin:6px 0">{idx.get("price", "")}</div>
                        <div style="font-size:11px;color:#5a5d6a">
                            开 {idx.get("open", "")} 高 {idx.get("high", "")} 低 {idx.get("low", "")}
                        </div>
                    </div>""", unsafe_allow_html=True)

        # 新闻
        st.markdown("<div style='font-size:15px;font-weight:600;color:#e6e9f0;margin:16px 0 8px'>相关要闻</div>",
                    unsafe_allow_html=True)
        if news_data:
            for n in news_data[:5]:
                src = n.get("source", "") or ""
                t = n.get("title", "")
                st.markdown(
                    f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:8px;
                              padding:10px;margin-bottom:6px;font-size:13px;line-height:1.4">
                        <div style="color:#e6e9f0">{t[:55]}</div>
                        <div style="color:#5a5d6a;font-size:11px;margin-top:4px">{src}</div>
                    </div>""", unsafe_allow_html=True)

        # AI 分析
        if ai_analysis:
            st.markdown("<div style='font-size:15px;font-weight:600;color:#e6e9f0;margin:12px 0 6px'>AI 分析</div>",
                        unsafe_allow_html=True)
            st.markdown(
                f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:8px;padding:12px;font-size:13px;color:#c5c8d4;line-height:1.5">{ai_analysis[:200]}</div>""",
                unsafe_allow_html=True)

    # 页脚
    st.markdown("<div style='margin-top:20px;font-size:11px;color:#3a3d4a;text-align:center'>数据来源: 天天基金 / 腾讯证券 / 新浪财经 | 自动刷新间隔 120 秒</div>",
                unsafe_allow_html=True)

