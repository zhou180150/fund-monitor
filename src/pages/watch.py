# watch.py - 盯盘页面（移动端优化）

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime


def _card_mobile(title, value, subtitle, color=None):
    val_color = f"color:{color};" if color else ""
    return f"""
    <div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:10px;padding:12px;margin-bottom:8px">
        <div style="font-size:11px;color:#8892b0;margin-bottom:4px">{title}</div>
        <div style="font-size:22px;font-weight:600;{val_color}">{value}</div>
        <div style="font-size:11px;color:#5a5d6a">{subtitle}</div>
    </div>"""


def _guess_sector(name):
    name = str(name)
    if any(k in name for k in ["贵州茅台", "五粮液", "洋河", "泸州老窖", "汾酒", "酒"]):
        return "白酒"
    if any(k in name for k in ["腾讯", "阿里", "百度", "美团", "京东", "网易", "拼多多"]):
        return "互联网"
    if any(k in name for k in ["招行", "平安", "兴业", "工商", "建设", "银行", "保险", "证券"]):
        return "金融"
    if any(k in name for k in ["宁德", "比亚迪", "隆基", "阳光电源", "亿纬", "新能源"]):
        return "新能源"
    if any(k in name for k in ["迈瑞", "恒瑞", "药明", "复星", "智飞", "医药", "医疗"]):
        return "医药"
    if any(k in name for k in ["美的", "格力", "海尔", "海康", "大华"]):
        return "家电/安防"
    if any(k in name for k in ["中芯", "韦尔", "北方华创", "兆易", "紫光", "海光", "芯片", "半导体"]):
        return "半导体"
    if any(k in name for k in ["紫金", "江西铜", "山东黄金", "中金黄金", "有色"]):
        return "有色"
    return "其他"


def render_watch_page(fund_data, stock_data, index_data, news_data, ai_analysis):
    # 标题行（紧凑）
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
            <div style="font-size:20px;font-weight:700;color:#e6e9f0">盯盘</div>
            <div style="font-size:10px;color:#5a5d6a;background:#1a1d29;padding:2px 8px;border-radius:4px">
                {datetime.now().strftime('%H:%M')}
            </div>
        </div>""", unsafe_allow_html=True)

    est = fund_data.get("estimate")

    # --- 核心指标：只两行卡片（移动端压缩） ---
    top_cards = []
    if est and "error" not in est:
        chg = est["estimate_change_pct"]
        c = "#00c853" if chg >= 0 else "#ff1744"
        arrow = "▲" if chg >= 0 else "▼"
        top_cards.append(("基金估值", f"{arrow} {chg:+.2f}%", f"{est['estimate_value']:.4f}", c))
    if index_data:
        idx = index_data[0] if isinstance(index_data, list) else index_data
        if "error" not in idx:
            c = "#00c853" if idx["change_pct"] >= 0 else "#ff1744"
            arrow = "▲" if idx["change_pct"] >= 0 else "▼"
            top_cards.append((idx.get("name", "沪深300"), f"{arrow} {idx['change_pct']:+.2f}%", f"{idx.get('price','')}", c))

    # 动态分列：手机 2 列，宽屏 4 列
    num = len(top_cards)
    if num > 0:
        cols = st.columns(min(num, 4))
        for i, (tt, tv, ts, tc) in enumerate(top_cards):
            with cols[i % len(cols)]:
                st.markdown(_card_mobile(tt, tv, ts, tc), unsafe_allow_html=True)

    # --- 持仓行情（简化为紧凑表格） ---
    if stock_data:
        rows = []
        for s in stock_data:
            if "error" not in s:
                chg = s.get("change_pct", 0)
                arrow = "▲" if chg >= 0 else "▼"
                rows.append({"股票": s.get("name", ""), "涨跌": f"{arrow} {chg:+.2f}%"})
        if rows:
            st.markdown("<div style='font-size:13px;font-weight:600;color:#e6e9f0;margin:8px 0 4px'>重仓股</div>", unsafe_allow_html=True)
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True,
                         column_config={
                             "股票": st.column_config.TextColumn(width="large"),
                             "涨跌": st.column_config.TextColumn(width="small"),
                         })
        else:
            st.caption("暂无重仓股实时行情")

    # --- 选项卡：净值图 / 持仓分布 / 新闻 AI ---
    tabs_names = ["📈 净值", "🥧 行业", "📰 新闻"]
    tab_charts, tab_pie, tab_news = st.tabs(tabs_names)

    with tab_charts:
        if fund_data.get("history"):
            df = pd.DataFrame(fund_data["history"])
            df["net_value"] = pd.to_numeric(df["net_value"], errors="coerce")
            fig = px.line(df, x="date", y="net_value")
            fig.update_layout(
                height=220, margin=dict(l=0, r=0, t=5, b=0),
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(color="#8892b0", size=9),
                xaxis=dict(showgrid=False, linecolor="#2a2d3a", tickangle=-45),
                yaxis=dict(showgrid=True, gridcolor="#1a1d29", linecolor="#2a2d3a"),
            )
            fig.update_traces(line=dict(color="#64b5f6", width=1.5))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with tab_pie:
        holdings = fund_data.get("holdings", [])
        if holdings:
            sector_map = {}
            for h in holdings:
                sector = _guess_sector(h.get("name", ""))
                sector_map[sector] = sector_map.get(sector, 0) + h.get("ratio", 0)
            df_sector = pd.DataFrame([{"行业": k, "占比": v} for k, v in sorted(sector_map.items(), key=lambda x: -x[1])])
            colors_pie = px.colors.qualitative.Set3[:len(df_sector)]
            fig_pie = go.Figure(data=[go.Pie(
                labels=df_sector["行业"], values=df_sector["占比"],
                marker=dict(colors=colors_pie),
                textinfo="label+percent",
                textfont=dict(size=10, color="#c5c8d4"),
                hole=0.4,
            )])
            fig_pie.update_layout(
                height=220, margin=dict(l=0, r=0, t=5, b=0),
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(color="#8892b0", size=10),
                showlegend=False,
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("暂无持仓数据")

    with tab_news:
        if news_data:
            for n in news_data[:4]:
                st.markdown(
                    f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:6px;
                              padding:8px;margin-bottom:4px;font-size:11px;line-height:1.3">
                        <div style="color:#e6e9f0">{n.get("title", "")[:50]}</div>
                        <div style="color:#5a5d6a;font-size:10px;margin-top:2px">{n.get("source", "")}</div>
                    </div>""", unsafe_allow_html=True)
        else:
            st.caption("暂无新闻")

        if ai_analysis:
            st.markdown("<div style='font-size:12px;font-weight:600;color:#64b5f6;margin:8px 0 4px'>AI 分析</div>", unsafe_allow_html=True)
            risk_text = ai_analysis.get("risk", "") if isinstance(ai_analysis, dict) else str(ai_analysis)
            st.markdown(
                f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:6px;padding:8px;font-size:11px;color:#c5c8d4;line-height:1.4">{risk_text[:200]}</div>""",
                unsafe_allow_html=True)
