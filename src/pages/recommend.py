# recommend.py - AI 推荐页面（移动端优化）

import streamlit as st
import pandas as pd


def render_recommend_page(ai):
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <div style="font-size:20px;font-weight:700;color:#e6e9f0">AI 推荐</div>
        <div style="font-size:10px;color:#5a5d6a;background:#1a1d29;padding:2px 8px;border-radius:4px">潜力基金</div>
    </div>""", unsafe_allow_html=True)

    # 筛选条件（紧凑横向）
    rcols = st.columns([1, 1, 1])
    with rcols[0]:
        rank_by = st.selectbox("维度", ["近1月", "近3月", "近6月", "近1年"], index=1, label_visibility="collapsed")
    with rcols[1]:
        top_n = st.selectbox("数量", [10, 20, 30, 50], index=1, label_visibility="collapsed")
    with rcols[2]:
        if st.button("▶ 分析", use_container_width=True, type="primary"):
            st.session_state.rank_result = None
            st.session_state.rank_loading = True

    if st.session_state.get("rank_loading"):
        with st.spinner("获取排行..."):
            from src.data.rank import get_fund_rank
            raw = get_fund_rank(page=1, per_page=top_n)

        if raw:
            with st.spinner("AI 评估..."):
                try:
                    ranks = "\n".join([
                        f"{i+1}. {r['name']}({r['code']}) 近1月:{r.get('month_return','N/A')}% "
                        f"近1年:{r.get('year_return','N/A')}%"
                        for i, r in enumerate(raw[:20])
                    ])
                    from src.analysis.knowledge import FUND_SELECTION_RULES
                    prompt = f"{FUND_SELECTION_RULES}\n\n请分析以下基金，按综合评分排序，推荐前5只，每只给评分和一句话理由：\n\n{ranks}"
                    result = ai.call_api("你是一个专业的基金分析师，严格按照评分规则打分。", prompt, max_tokens=1000)
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

        # AI 推荐结果
        st.markdown("<div style='font-size:12px;font-weight:600;color:#64b5f6;margin:8px 0 4px'>AI 推荐</div>", unsafe_allow_html=True)
        st.markdown(
            f"""<div style="background:#1a1d29;border:1px solid #2a2d3a;border-radius:8px;padding:10px;font-size:11px;line-height:1.5;color:#c5c8d4">{ai_text}</div>""",
            unsafe_allow_html=True)

        # 排行表格（紧凑）
        if raw_list:
            rows = []
            for i, r in enumerate(raw_list[:20]):
                rows.append({
                    "#": i + 1,
                    "名称": r["name"][:12],
                    "近1月": f"{r.get('month_return','N/A')}%",
                    "近1年": f"{r.get('year_return','N/A')}%",
                })
            df = pd.DataFrame(rows)
            st.markdown("<div style='font-size:12px;font-weight:600;color:#e6e9f0;margin:8px 0 4px'>全市场排行</div>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("选择条件后点击 ▶ 分析")
