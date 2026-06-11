# recommend.py - AI 推荐页面（双模式：排行榜 + 新闻驱动）

import streamlit as st
import pandas as pd


def render_recommend_page(ai):
    st.markdown(
        "<div style='display:flex;align-items:center;gap:8px;margin-bottom:8px'>"
        "<div style='font-size:20px;font-weight:700;color:#e6e9f0'>AI 推荐</div>"
        "<div style='font-size:10px;color:#5a5d6a;background:#1a1d29;padding:2px 8px;border-radius:4px'>双引擎分析</div>"
        "</div>", unsafe_allow_html=True)

    tab_rank, tab_news = st.tabs(["排行榜推荐", "新闻驱动推荐"])

    # ========== 排行榜推荐 ==========
    with tab_rank:
        rcols = st.columns([1, 1, 1])
        with rcols[0]:
            rank_by = st.selectbox("维度", ["近1月", "近3月", "近6月", "近1年"], index=1, label_visibility="collapsed", key="rb")
        with rcols[1]:
            top_n = st.selectbox("数量", [10, 20, 30, 50], index=1, label_visibility="collapsed", key="tn")
        with rcols[2]:
            if st.button("排行分析", use_container_width=True, type="primary", key="rb_btn"):
                st.session_state.rank_result = None
                st.session_state.rank_loading = True

        if st.session_state.get("rank_loading"):
            with st.spinner("获取排行..."):
                from src.data.rank import get_fund_rank, enrich_rank_data
                raw = get_fund_rank(page=1, per_page=top_n)
            if raw:
                with st.spinner("AI 评估..."):
                    try:
                        enriched = enrich_rank_data(raw[:20])
                        ranks = "\n".join([f"{i+1}. {r['name']}({r['code']}) 近1月:{r.get('month_return','N/A')}% 近3月:{r.get('quarter_return','N/A')}% 近1年:{r.get('year_return','N/A')}% 回撤30日:{r.get('max_drawdown_30d','N/A')}% 回撤90日:{r.get('max_drawdown_90d','N/A')}% 波动率:{r.get('volatility_20d','N/A')}% 集中度:{r.get('top3_concentration','N/A')}% 规模:{r.get('scale','N/A')} 经理:{r.get('manager_tenure','N/A')}" for i, r in enumerate(enriched)])
                        from src.analysis.knowledge import FUND_SELECTION_RULES
                        prompt = f"{FUND_SELECTION_RULES}\n\n请分析以下基金，按综合评分排序，推荐前5只，每只给评分和一句话理由：\n\n{ranks}"
                        result = ai.call_api("你是一个专业的基金分析师，严格按照评分规则打分。", prompt, max_tokens=1000)
                        st.session_state.rank_result = {"raw": enriched, "ai_analysis": result}
                        try:
                            from src.data.db import save_ranking
                            save_ranking(rank_by, enriched)
                        except Exception:
                            pass
                    except Exception as e:
                        st.session_state.rank_result = {"raw": enriched, "ai_analysis": f"[AI分析失败: {e}]"}
                    st.session_state.rank_loading = False
                st.rerun()

        result = st.session_state.get("rank_result")
        if result:
            ai_text = result.get("ai_analysis", "")
            st.markdown("<div style='font-size:12px;font-weight:600;color:#64b5f6;margin:8px 0 4px'>AI 评分推荐</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background:#1a1d29;border:1px solid #2a2d3a;border-radius:8px;padding:10px;font-size:11px;line-height:1.5;color:#c5c8d4'>{ai_text}</div>", unsafe_allow_html=True)
            if result.get("raw"):
                rows = [{"#": i+1, "名称": r["name"][:12], "近1月": f"{r.get('month_return','N/A')}%", "近1年": f"{r.get('year_return','N/A')}%"} for i, r in enumerate(result["raw"][:20])]
                st.markdown("<div style='font-size:12px;font-weight:600;color:#e6e9f0;margin:8px 0 4px'>全市场排行参考</div>", unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("选择条件后点击排行分析。注意：排行榜基金已涨过，追高有风险")

    # ========== 新闻驱动推荐 ==========
    with tab_news:
        st.markdown("<div style='background:#1a1d29;border:1px solid #2a2d3a;border-radius:8px;padding:10px;font-size:11px;color:#8892b0;margin-bottom:10px'>基于今日实时新闻分析，推荐低位有催化剂的板块和基金。<br>不依赖排行榜，避免追涨杀跌。</div>", unsafe_allow_html=True)

        if st.button("分析今日新闻", use_container_width=True, type="primary"):
            st.session_state.news_driven_loading = True

        if st.session_state.get("news_driven_loading"):
            news_cache = st.session_state.get("_news_cache", [])
            funds_cache = st.session_state.get("_funds_cache", {})
            index_cache = st.session_state.get("_index_cache", [])

            if not news_cache:
                from src.data.news import fetch_market_news
                news_cache = fetch_market_news()
                from src.data.news import filter_news_by_keywords
                news_cache = filter_news_by_keywords(news_cache, ["基金", "A股", "市场", "股市", "行情", "投资"])

            if not news_cache:
                st.warning("今日暂无新闻数据，请稍后再试")
                st.session_state.news_driven_loading = False
            else:
                with st.spinner("AI 分析新闻中..."):
                    funds_data_list = [{"code": code, "est": fd.get("estimate"), "hist": fd.get("history"), "holdings": fd.get("holdings")} for code, fd in funds_cache.items()]
                    result = ai.news_driven_recommend(news_cache, index_cache, funds_data_list)
                    st.session_state.news_driven_result = result
                    st.session_state.news_driven_loading = False
                st.rerun()

        news_result = st.session_state.get("news_driven_result")
        if news_result:
            st.markdown("<div style='font-size:12px;font-weight:600;color:#64b5f6;margin:8px 0 4px'>AI 新闻分析</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background:#1a1d29;border:1px solid #2a2d3a;border-radius:8px;padding:12px;font-size:11px;line-height:1.6;color:#c5c8d4;white-space:pre-wrap'>{news_result}</div>", unsafe_allow_html=True)
