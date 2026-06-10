import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

def _calc_metrics(daily_chg_series):
    """计算基金指标：夏普比率、波动率、最大回撤、胜率"""
    chgs = daily_chg_series.dropna()
    if len(chgs) < 5:
        return {}
    vol = chgs.std() * np.sqrt(252)  # 年化波动率
    sharpe = (chgs.mean() / chgs.std() * np.sqrt(252)) if chgs.std() > 0 else 0
    cumulative = (1 + chgs / 100).cumprod()
    rolling_max = cumulative.expanding().max()
    dd = ((cumulative - rolling_max) / rolling_max * 100).min()
    wr = (chgs > 0).sum() / len(chgs) * 100
    return {
        "年化波动率": f"{vol:.1f}%",
        "夏普比率": f"{sharpe:.2f}",
        "区间最大回撤": f"{dd:.1f}%",
        "胜率": f"{wr:.0f}%",
    }

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

    # 横向指标对比表（含夏普比率、波动率）
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
            metrics = _calc_metrics(daily_chg)
            row = {"基金": fund_data.get("name", fund_code)[:15]}
            row["近5日"] = f"{daily_chg.tail(5).sum():+.2f}%" if len(daily_chg) >= 5 else "N/A"
            row["近20日"] = f"{daily_chg.tail(20).sum():+.2f}%" if len(daily_chg) >= 20 else "N/A"
            row.update(metrics)
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
            row = {"基金": "沪深300 (基准)"}
            row["近5日"] = f"{da.tail(5).sum():+.2f}%" if len(da) >= 5 else "N/A"
            row["近20日"] = f"{da.tail(20).sum():+.2f}%" if len(da) >= 20 else "N/A"
            row.update(idx_metrics)
            rows.append(row)

    if rows:
        df_table = pd.DataFrame(rows)
        # 高亮夏普比率
        html_rows = ""
        columns = df_table.columns.tolist()
        for _, r in df_table.iterrows():
            cells = ""
            for col in columns:
                val = r[col]
                color = "#e6e9f0"
                if col in ("近5日", "近20日"):
                    try:
                        v = float(str(val).replace("%", "").replace("N/A", "0"))
                        color = "#00c853" if v >= 0 else "#ff1744"
                    except:
                        pass
                if col == "夏普比率":
                    try:
                        sv = float(str(val))
                        color = "#00c853" if sv > 0.5 else ("#ff9800" if sv > 0 else "#ff1744")
                    except:
                        pass
                cells += f'<td style="padding:8px 12px;color:{color};border-bottom:1px solid #1a1d29">{val}</td>'
            html_rows += f"<tr><td style='padding:8px 12px;color:#e6e9f0;border-bottom:1px solid #1a1d29;font-weight:500'>{r['基金']}</td>{cells}</tr>"

        headers = "".join([f'<th style="padding:10px 12px;text-align:left;color:#8892b0;font-weight:500">{c}</th>' for c in columns])
        st.markdown(f"""
        <div style="background:#0e1117;border:1px solid #2a2d3a;border-radius:10px;overflow-x:auto">
            <table style="width:100%;border-collapse:collapse;font-size:12px;min-width:600px">
                <thead><tr style="background:#1a1d29">{headers}</tr></thead>
                <tbody>{html_rows}</tbody>
            </table>
        </div>""", unsafe_allow_html=True)

    # 夏普比率条形图
    if rows:
        st.markdown("<div style='margin:12px 0'></div>", unsafe_allow_html=True)
        sharpes = [r for r in rows if r.get("夏普比率") and r["夏普比率"] != "N/A"]
        if sharpes:
            fig_sharpe = go.Figure()
            for r in sharpes:
                try:
                    sv = float(r["夏普比率"])
                    color = "#00c853" if sv > 0.5 else ("#ff9800" if sv > 0 else "#ff1744")
                    fig_sharpe.add_trace(go.Bar(
                        x=[r["基金"]], y=[sv],
                        marker_color=color,
                        text=f"{sv:.2f}", textposition="outside",
                        textfont=dict(size=11),
                        width=0.5,
                    ))
                except:
                    pass
            fig_sharpe.update_layout(
                title=dict(text="夏普比率对比", font=dict(color="#8892b0", size=13)),
                height=250, margin=dict(l=0, r=0, t=30, b=0),
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(color="#8892b0", size=11),
                xaxis=dict(showgrid=False, linecolor="#2a2d3a"),
                yaxis=dict(showgrid=True, gridcolor="#1a1d29", linecolor="#2a2d3a", title="夏普比率"),
                showlegend=False,
            )
            st.plotly_chart(fig_sharpe, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='margin-top:16px;font-size:11px;color:#3a3d4a;text-align:center'>夏普比率 > 0.5 良好, > 1 优秀 | 基准为沪深300</div>", unsafe_allow_html=True)
