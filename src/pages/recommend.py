# recommend.py - AI 潜力基金推荐页面

import streamlit as st
import pandas as pd
from datetime import datetime


def render_recommend_page(ai):
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
        <div style="font-size:28px;font-weight:700;color:#e6e9f0">AI 推荐</div>
        <div style="font-size:12px;color:#5a5d6a;background:#1a1d29;padding:4px 10px;border-radius:6px">潜力基金</div>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("<div style='font-size:14px;font-weight:600;color:#e6e9f0;margin-bottom:10px'>筛选条件</div>",
                    unsafe_allow_html=True)

        rank_by = st.selectbox("排行维度", ["近1月", "近3月", "近6月", "近1年"], index=1)
        top_n = st.selectbox("取前多少只", [10, 20, 30, 50], index=1)

        if st.button("开始分析", use_container_width=True, type="primary"):
            st.session_state.rank_result = None
            st.session_state.rank_loading = True

    if st.session_state.get("rank_loading"):
        with st.spinner("获取全市场排行..."):
            from src.data.rank import get_fund_rank
            # 获取近3月排行（参数映射）
            raw = get_fund_rank(page=1, per_page=top_n)

        if raw:
            with st.spinner("AI 评估中..."):
                try:
                    ranks = "\n".join([
                        f"{i+1}. {r['name']}({r['code']}) 近1月:{r.get('month_return','N/A')}% "
                        f"近1年:{r.get('year_return','N/A')}%"
                        for i, r in enumerate(raw[:20])
                    ])
                    from src.analysis.knowledge import FUND_SELECTION_RULES
                    prompt = f"{FUND_SELECTION_RULES}\n\n请分析以下基金，按综合评分从高到低排序，推荐前5只，每只给出评分和一句话理由：\n\n{ranks}"
                    result = ai.call_api(
                        "你是一个专业的基金分析师，严格按照评分规则打分。",
                        prompt, max_tokens=1000
                    )
                    st.session_state.rank_result = {"raw": raw[:20], "ai_analysis": result}
                    try:
                        from src.data.db import save_ranking
                        save_ranking(rank_by, raw[:20])
                    except Exception:
                        pass
                except Exception as e:
                    st.session_state.rank_result = {"raw": raw[:20], "ai_analysis": f"[AI分析失败: {e}]"}
                st.session_state.rank_loading = False
            st.rerun()

    result = st.session_state.get("rank_result")
    if result:
        raw_list = result.get("raw", [])
        ai_text = result.get("ai_analysis", "")

        with col2:
            st.markdown("<div style='font-size:14px;font-weight:600;color:#e6e9f0;margin-bottom:8px'>AI 推荐结果</div>",
                        unsafe_allow_html=True)
            st.markdown(
                f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:10px;padding:14px;font-size:13px;line-height:1.6;color:#c5c8d4">{ai_text}</div>""",
                unsafe_allow_html=True)

        # 原始排行数据
        if raw_list:
            st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
            rows = []
            for i, r in enumerate(raw_list[:20]):
                chg = r.get("daily_change", "N/A")
                c = "#00c853" if chg and chg.startswith("-") else "#ff1744"
                rows.append({
                    "排名": i + 1,
                    "基金名称": r["name"],
                    "代码": r["code"],
                    "近1月": f"{r.get('month_return','')}%",
                    "近1年": f"{r.get('year_return','')}%",
                })
            df = pd.DataFrame(rows)
            st.markdown("<div style='font-size:14px;font-weight:600;color:#e6e9f0;margin:10px 0 8px'>全市场排行参考</div>",
                        unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        with col2:
            st.info('选择筛选条件后点击 开始分析 获取AI推荐')

    st.markdown("<div style='margin-top:16px;font-size:11px;color:#3a3d4a;text-align:center'>数据来源: 天天基金排行榜 | AI评分仅供参考</div>",
                unsafe_allow_html=True)
