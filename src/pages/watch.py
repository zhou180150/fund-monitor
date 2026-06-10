# watch.py - 盯盘页面

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime


def _card(title, value, subtitle, color=None, extra=None):
    val_color = f"color:{color};" if color else ""
    extra_html = f"<div style='font-size:12px;color:#8892b0;margin-top:4px'>{extra}</div>" if extra else ""
    return f"""
    <div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:12px;padding:16px;margin-bottom:10px">
        <div style="font-size:13px;color:#8892b0;margin-bottom:6px">{title}</div>
        <div style="font-size:28px;font-weight:600;{val_color}">{value}</div>
        <div style="font-size:13px;color:#5a5d6a">{subtitle}</div>
        {extra_html}
    </div>"""


def _guess_sector(name):
    """简单行业分类"""
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
    if any(k in name for k in ["中石油", "中石化", "中海油", "中国神华", "陕西煤业", "能源"]):
        return "能源"
    if any(k in name for k in ["万科", "保利", "招商蛇口", "地产"]) and "保险" not in name:
        return "地产"
    if any(k in name for k in ["中芯", "韦尔", "北方华创", "兆易", "紫光", "海光", "芯片", "半导体"]):
        return "半导体"
    if any(k in name for k in ["中航", "航发", "航天", "沈飞", "西飞", "军工"]):
        return "军工"
    if any(k in name for k in ["紫金", "江西铜", "山东黄金", "中金黄金", "有色"]):
        return "有色"
    return "其他"


def render_watch_page(fund_data, stock_data, index_data, news_data, ai_analysis):
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
        <div style="font-size:28px;font-weight:700;color:#e6e9f0">盯盘</div>
        <div style="font-size:12px;color:#5a5d6a;background:#1a1d29;padding:4px 10px;border-radius:6px">
            """ + f"{datetime.now().strftime('%H:%M')} 更新" + """
        </div>
    </div>""", unsafe_allow_html=True)

    # 关键指标卡片
    est = fund_data.get("estimate")
    cards = []
    if est and "error" not in est:
        chg = est["estimate_change_pct"]
        c = "#00c853" if chg >= 0 else "#ff1744"
        arrow = "▲" if chg >= 0 else "▼"
        cards.append((
            est.get("name", "基金"),
            f"{arrow} {chg:+.2f}%",
            f"估值 {est['estimate_value']:.4f} | 净值 {est['net_value']:.4f}",
            c, est.get("estimate_time", ""),
        ))
    else:
        cards.append(("基金", "N/A", "非交易时段", "#5a5d6a", ""))

    if index_data:
        idx = index_data[0] if isinstance(index_data, list) else index_data
        if "error" not in idx:
            c = "#00c853" if idx["change_pct"] >= 0 else "#ff1744"
            arrow = "▲" if idx["change_pct"] >= 0 else "▼"
            cards.append((idx.get("name", "沪深300"), f"{arrow} {idx['change_pct']:+.2f}%", f"{idx.get('price', '')}", c))

    stock_count = len([s for s in (stock_data or []) if "error" not in s])
    news_count = len(news_data or [])
    cards.append(("监控概览", f"{stock_count} 只股票", f"{news_count} 条新闻", "#64b5f6", ""))
    cards.append(("更新时间", datetime.now().strftime("%H:%M:%S"), "自动刷新 120s", "#8892b0", ""))

    cols = st.columns(len(cards))
    for i, (title, val, sub, color, *extra) in enumerate(cards):
        with cols[i]:
            st.markdown(_card(title, val, sub, color, extra[0] if extra else None), unsafe_allow_html=True)

    # 双列布局
    col1, col2 = st.columns([1.2, 1])

    with col1:
        if fund_data.get("history"):
            st.markdown("<div style='font-size:15px;font-weight:600;color:#e6e9f0;margin-bottom:8px'>净值走势</div>", unsafe_allow_html=True)
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

        # 持仓行业分布饼图
        holdings = fund_data.get("holdings", [])
        if holdings:
            st.markdown("<div style='font-size:15px;font-weight:600;color:#e6e9f0;margin:12px 0 8px'>持仓行业分布</div>", unsafe_allow_html=True)
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
                textfont=dict(size=11, color="#c5c8d4"),
                hole=0.4,
            )])
            fig_pie.update_layout(
                height=280, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(color="#8892b0", size=11),
                showlegend=False,
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

        if stock_data:
            st.markdown("<div style='font-size:15px;font-weight:600;color:#e6e9f0;margin:12px 0 8px'>重仓股实时</div>", unsafe_allow_html=True)
            rows = []
            for s in stock_data:
                if "error" not in s:
                    chg = s.get("change_pct", 0)
                    arrow = "▲" if chg >= 0 else "▼"
                    c = "#00c853" if chg >= 0 else "#ff1744"
                    rows.append({"股票": s.get("name", ""), "现价": s.get("price", ""), " ": f"{arrow} {chg:+.2f}%"})
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

        st.markdown("<div style='font-size:15px;font-weight:600;color:#e6e9f0;margin:16px 0 8px'>相关要闻</div>", unsafe_allow_html=True)
        if news_data:
            for n in news_data[:5]:
                st.markdown(
                    f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:8px;
                              padding:10px;margin-bottom:6px;font-size:13px;line-height:1.4">
                        <div style="color:#e6e9f0">{n.get("title", "")[:55]}</div>
                        <div style="color:#5a5d6a;font-size:11px;margin-top:4px">{n.get("source", "")}</div>
                    </div>""", unsafe_allow_html=True)

        if ai_analysis:
            st.markdown("<div style='font-size:15px;font-weight:600;color:#e6e9f0;margin:12px 0 6px'>AI 分析</div>", unsafe_allow_html=True)
            risk_text = ai_analysis.get("risk", "") if isinstance(ai_analysis, dict) else str(ai_analysis)
            st.markdown(
                f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:8px;padding:12px;font-size:13px;color:#c5c8d4;line-height:1.5">{risk_text[:300]}</div>""",
                unsafe_allow_html=True)

    st.markdown("<div style='margin-top:20px;font-size:11px;color:#3a3d4a;text-align:center'>数据来源: 天天基金 / 腾讯证券 / 新浪财经 | 自动刷新间隔 120 秒</div>", unsafe_allow_html=True)
