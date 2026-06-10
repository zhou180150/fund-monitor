import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

def render_compare_page(all_funds_data, index_history):
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
        <div style="font-size:28px;font-weight:700;color:#e6e9f0">对比</div>
        <div style="font-size:12px;color:#5a5d6a;background:#1a1d29;padding:4px 10px;border-radius:6px">多基金 + 基准</div>
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
            name = fund_data.get("name", fund_code)[:12]
            fig.add_trace(go.Scatter(
                x=df["date"], y=df["net_value"],
                mode="lines", name=name,
                line=dict(width=2.5),
            ))

    # 基准线
    if index_history:
        df_idx = pd.DataFrame(index_history)
        if not df_idx.empty:
            fig.add_trace(go.Scatter(
                x=df_idx["date"], y=df_idx["close"],
                mode="lines", name="沪深300",
                line=dict(color="rgba(255,183,77,0.7)", width=2, dash="dash"),
            ))

    fig.update_layout(
        height=400, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
        font=dict(color="#8892b0", size=11),
        xaxis=dict(showgrid=False, linecolor="#2a2d3a"),
        yaxis=dict(showgrid=True, gridcolor="#1a1d29", linecolor="#2a2d3a"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # 近期表现对比表
    st.markdown("<div style='margin:12px 0'></div>", unsafe_allow_html=True)
    rows = []
    for fund_code, fund_data in all_funds_data.items():
        if fund_data.get("history"):
            df = pd.DataFrame(fund_data["history"])
            daily_chg = pd.to_numeric(
                df["daily_change_pct"].apply(
                    lambda x: x.replace("%", "") if isinstance(x, str) else x
                ), errors="coerce"
            )
            # 统一到同一时间窗口
            rows.append({
                "基金": fund_data.get("name", fund_code)[:15],
                "近5日": f"{daily_chg.tail(5).sum():+.2f}%",
                "近20日": f"{daily_chg.tail(20).sum():+.2f}%" if len(daily_chg) >= 20 else "N/A",
                "单日最大涨幅": f"{daily_chg.max():+.2f}%",
                "单日最大回撤": f"{daily_chg.min():+.2f}%",
            })

    # 添加基准到对比表
    if index_history:
        df_idx = pd.DataFrame(index_history)
        daily_idx = []
        for i in range(1, len(df_idx)):
            if df_idx.iloc[i]["close"] and df_idx.iloc[i-1]["close"]:
                chg = (df_idx.iloc[i]["close"] - df_idx.iloc[i-1]["close"]) / df_idx.iloc[i-1]["close"] * 100
                daily_idx.append(chg)
        if daily_idx:
            da = pd.Series(daily_idx)
            rows.append({
                "基金": "沪深300 (基准)",
                "近5日": f"{da.tail(5).sum():+.2f}%",
                "近20日": f"{da.tail(20).sum():+.2f}%" if len(da) >= 20 else "N/A",
                "单日最大涨幅": f"{da.max():+.2f}%",
                "单日最大回撤": f"{da.min():+.2f}%",
            })

    if rows:
        df_table = pd.DataFrame(rows)
        # 用 HTML 渲染更美观
        html_rows = ""
        for _, r in df_table.iterrows():
            name = r["基金"]
            c5 = "#00c853" if float(r["近5日"].replace("%","")) >= 0 else "#ff1744"
            c20 = "#00c853" if float(r["近20日"].replace("%","")) >= 0 else "#ff1744"
            html_rows += f"""
            <tr>
                <td style="padding:8px 12px;color:#e6e9f0;border-bottom:1px solid #1a1d29;font-weight:500">{name}</td>
                <td style="padding:8px 12px;color:{c5};border-bottom:1px solid #1a1d29">{r['近5日']}</td>
                <td style="padding:8px 12px;color:{c20};border-bottom:1px solid #1a1d29">{r['近20日']}</td>
                <td style="padding:8px 12px;color:#00c853;border-bottom:1px solid #1a1d29">{r['单日最大涨幅']}</td>
                <td style="padding:8px 12px;color:#ff1744;border-bottom:1px solid #1a1d29">{r['单日最大回撤']}</td>
            </tr>"""
        st.markdown(f"""
        <div style="background:#0e1117;border:1px solid #2a2d3a;border-radius:10px;overflow:hidden">
            <table style="width:100%;border-collapse:collapse;font-size:13px">
                <thead>
                    <tr style="background:#1a1d29">
                        <th style="padding:10px 12px;text-align:left;color:#8892b0;font-weight:500">基金</th>
                        <th style="padding:10px 12px;text-align:left;color:#8892b0;font-weight:500">近5日</th>
                        <th style="padding:10px 12px;text-align:left;color:#8892b0;font-weight:500">近20日</th>
                        <th style="padding:10px 12px;text-align:left;color:#8892b0;font-weight:500">最大日涨</th>
                        <th style="padding:10px 12px;text-align:left;color:#8892b0;font-weight:500">最大日跌</th>
                    </tr>
                </thead>
                <tbody>{html_rows}</tbody>
            </table>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:16px;font-size:11px;color:#3a3d4a;text-align:center'>基准为沪深300指数 | 数据来源: 天天基金 / 腾讯证券</div>",
                unsafe_allow_html=True)

