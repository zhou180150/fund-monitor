# TODO

## 部署
- [ ] 在 GitHub 创建仓库 `fund-monitor`（Private）
- [ ] 推代码到 GitHub
- [ ] 在 Streamlit Cloud 部署
  - 分支: main
  - 入口: app_v2.py
  - Secrets: DEEPSEEK_API_KEY

## 数据库
- [x] SQLite 四张表已建好
- [x] fund_snapshots 自动写入（每2分钟）
- [x] ai_reports 自动写入
- [x] chat_logs 自动写入
- [x] daily_rankings 自动写入
- [ ] 接入 AI 分析时能从数据库读历史趋势

## 功能增强
- [ ] 持仓行业分布饼图（盯盘页）
- [ ] 近30日回撤趋势图（复盘页）
- [ ] 基金对比页增加夏普比率、波动率指标
- [ ] 推送通道（飞书/邮件每日报告）

## UI
- [x] 深色主题 CSS
- [x] 侧边栏 AI 管家聊天区
- [x] 导航 Tab 样式
- [ ] 移动端适配

## AI 管家
- [x] knowledge.py 技术库（开源项目规则提炼）
- [x] advisor.py 分析引擎
- [x] 侧边栏对话入口
- [ ] 定期自动推送分析（无需用户手动点）
- [ ] 回答时引用历史数据（"近30天回撤处于中等水平"）
