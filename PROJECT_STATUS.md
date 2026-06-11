# 项目状态记录 (2026-06-11)

## 本地服务
- 地址: http://localhost:8620
- 入口: app_v2.py
- 运行: streamlit run app_v2.py --server.port 8620

## 部署
- Streamlit Cloud: https://zhou180150-fund-monitor-app-v2-9ryt9v.streamlit.app
- GitHub: https://github.com/zhou180150/fund-monitor
- 目录: D:und_monitor

## 关键配置
- DeepSeek API Key: 在 Streamlit Cloud Secrets 中配置
- 基金: 110011 (易方达优质精选), 005827 (易方达蓝筹精选)
- 数据库: cache/fund_monitor.db (SQLite)

## 模块说明
- app_v2.py: 入口，全局 CSS，侧边栏 AI 聊天
- src/data/: fund/stock/news/rank 数据获取
- src/analysis/: advisor/knowledge/sector_map 分析层
- src/pages/: watch(盯盘)/review(复盘)/compare(对比)/recommend(推荐)
- src/data/db.py: SQLite 持久化
- src/push.py: 推送预留

## AI 数据共享 (st.session_state.ai_memory)
- daily_risk/daily_market: AI 日报结论
- last_rank_analysis: 排行榜分析结果
- last_news_recommend: 新闻推荐结果
- chat_summary: 对话上下文
