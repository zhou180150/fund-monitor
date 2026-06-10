# 基金监控看板

AI 驱动的中国基金实时监控与智能分析系统。

## 功能

- **📡 盯盘**：盘中实时估值 + 重仓股实时行情 + 大盘指数 + 相关要闻 + 持仓行业分布饼图
- **📊 复盘**：净值曲线 + 回撤趋势图（带警戒线/止损线）+ 日涨跌幅 + 关键指标（胜率、回撤、波动率）+ AI 研判
- **⚖️ 对比**：多只基金同屏对比 + 与沪深300基准对比 + 夏普比率 + 年化波动率
- **🎯 推荐**：全市场基金排行 + AI 智能评分推荐（按评分规则）
- **🤖 AI 管家**：侧边栏实时对话 + 快提问按钮 + 每日风险分析 + 市场情绪判断
- **🗄️ 数据库**：SQLite 自动存储估值快照、排行、AI 报告、对话记录（按日去重，自动清理过期数据）

## 数据源

| 数据 | 来源 |
|------|------|
| 基金净值/估值 | 天天基金 (fund.eastmoney.com) |
| 股票行情 | 腾讯证券 (qt.gtimg.cn) |
| 大盘指数 K 线 | 腾讯财经 K 线 API |
| 财经新闻 | 新浪财经滚动新闻 |
| AI 分析 | DeepSeek API |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 修改 config.json，填入你的基金代码

# 3. 启动看板
streamlit run app_v2.py
```

## 配置说明

编辑 `config.json`：

- `funds`：关注的基金列表（code + name）
- `benchmark`：对比基准指数代码
- `refresh_interval_seconds`：自动刷新间隔
- `deepseek_api_key`：DeepSeek API Key（可选，也可通过环境变量 `DEEPSEEK_API_KEY` 设置）

## 部署到 Streamlit Cloud

1. 推送到 GitHub
2. 在 [Streamlit Cloud](https://share.streamlit.io) 选择仓库和入口文件 `app_v2.py`
3. 在 Secrets 中添加 `DEEPSEEK_API_KEY=sk-xxx`

## 项目结构

```
fund_monitor/
├── app_v2.py              # 主入口
├── config.json            # 配置
├── requirements.txt       # 依赖
├── .streamlit/config.toml # Streamlit 配置
├── src/
│   ├── data/
│   │   ├── fund.py        # 基金净值/估值/持仓
│   │   ├── stock.py       # 股票/指数行情
│   │   ├── news.py        # 财经新闻
│   │   ├── rank.py        # 基金排行
│   │   └── db.py          # SQLite 数据库
│   ├── analysis/
│   │   ├── advisor.py     # AI 分析引擎
│   │   ├── indicators.py  # 技术指标计算
│   │   └── knowledge.py   # 分析规则库
│   └── pages/
│       ├── watch.py       # 盯盘页
│       ├── review.py      # 复盘页
│       ├── compare.py     # 对比页
│       └── recommend.py   # 推荐页
└── cache/                 # SQLite 数据库目录
```

## 后续计划

- 持仓行业分布饼图 ✅
- 回撤趋势图 ✅
- 夏普比率对比 ✅
- 数据库按日去重 ✅
- 移动端适配 ✅
- 推送到 Lark/邮件每日报告
- AI 回答时引用历史数据库趋势
- 定期自动推送分析（无需手动触发）

## 注意事项

- 交易时段（9:30-15:00）估值数据可用
- 非交易时段显示 N/A
- AI 分析需要有效的 DeepSeek API Key
- 数据库自动保留：快照 30 天 / 排行 90 天 / AI 报告 180 天 / 聊天记录 7 天
