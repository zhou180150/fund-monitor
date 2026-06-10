# 基金监控看板

## 功能
-   **盯盘**：盘中实时估值 + 重仓股行情 + 大盘指数 + 相关新闻
-   **复盘**：净值曲线 + 涨跌幅 + 关键指标（胜率、回撤）+ AI 今日研判
-   **对比**：多只基金同屏对比 + 与沪深300基准对比

## 数据源
- **基金净值/估值**：天天基金 (fund.eastmoney.com)
- **股票行情**：腾讯证券 (qt.gtimg.cn)
- **新闻**：新浪财经滚动新闻
- **AI 分析**：DeepSeek API

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 修改 config.json，填入你的基金代码

# 3. 启动看板
streamlit run app.py
```

## 配置说明

编辑 `config.json`：

- `funds`：关注的基金列表（code + name）
- `benchmark`：对比基准指数代码
- `refresh_interval_seconds`：自动刷新间隔
- `deepseek_api_key`：DeepSeek API Key（可选，不填则无AI分析）

## 项目结构

```
fund_monitor/
├── app.py                 # 入口
├── config.json            # 配置
├── requirements.txt       # 依赖
├── src/
│   ├── data/
│   │   ├── fund.py        # 基金数据
│   │   ├── stock.py       # 股票行情
│   │   └── news.py        # 新闻
│   ├── analysis/
│   │   ├── indicators.py  # 技术指标
│   │   └── deepseek.py    # AI分析
│   └── pages/
│       ├── watch.py       # 盯盘页
│       ├── review.py      # 复盘页
│       └── compare.py     # 对比页
└── cache/                 # 数据缓存
```

## 注意事项
- 交易时段（9:30-15:00）估值数据可用
- 新闻仅抓取新浪财经滚动新闻，如需深度搜索请自行扩展
- AI 分析需要有效的 DeepSeek API Key
