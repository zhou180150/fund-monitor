# advisor.py - AI 管家：基于技术知识库 + 新闻驱动的基金分析
import json
import requests
import numpy as np
from .knowledge import (
    FUND_RISK_RULES, MARKET_RULES, FUND_SELECTION_RULES,
    OPERATION_ADVICE, AI_ANALYSIS_PROMPT, NEWS_DRIVEN_RULES
)


class AIAdvisor:
    def __init__(self, api_key, model="deepseek-v4-flash"):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.deepseek.com/chat/completions"

    def call_api(self, system_prompt, user_prompt, max_tokens=800, model=None):
        if not self.api_key:
            return "API key 未配置"
        try:
            r = requests.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model or self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": max_tokens,
                },
                timeout=60,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[AI请求失败: {e}]"

    def _calc_indicators(self, fund_data):
        est = fund_data.get("est", {})
        hist = fund_data.get("hist", [])
        holds = fund_data.get("holdings", [])
        daily_chgs = []
        for h in hist[-30:]:
            try:
                v = float(h.get("daily_change_pct", 0))
                daily_chgs.append(v)
            except:
                daily_chgs.append(0)
        net_values = []
        for h in hist[-30:]:
            try:
                v = float(h.get("net_value", 0))
                if v > 0:
                    net_values.append(v)
            except:
                pass
        dd_30d = 0
        if net_values:
            peak = net_values[0]
            for v in net_values:
                if v > peak:
                    peak = v
                d = (peak - v) / peak * 100
                if d > dd_30d:
                    dd_30d = d
        vol_20d = np.std(daily_chgs[-20:]) * np.sqrt(252) if len(daily_chgs) >= 5 else 0
        top3 = sum(h.get("ratio", 0) for h in holds[:3])
        ma_trend = "未知"
        if len(net_values) >= 20:
            ma5 = sum(net_values[-5:]) / 5
            ma10 = sum(net_values[-10:]) / 10
            ma20 = sum(net_values[-20:]) / 20
            latest = net_values[-1]
            below_count = sum(1 for m in [ma5, ma10, ma20] if latest < m)
            if below_count == 0:
                ma_trend = "在各均线上方（强势）"
            elif below_count == 1:
                ma_trend = "跌破MA5（短线走弱）"
            elif below_count >= 2:
                ma_trend = "跌破多条均线（趋势走坏）"
        ret_5d = sum(daily_chgs[-5:]) if len(daily_chgs) >= 5 else 0
        ret_30d = sum(daily_chgs[-30:]) if len(daily_chgs) >= 30 else sum(daily_chgs)
        return {
            "name": est.get("name", fund_data.get("code", "")),
            "estimate_value": est.get("estimate_value", "N/A"),
            "today_change": est.get("estimate_change_pct", "N/A"),
            "dd_30d": round(dd_30d, 2),
            "volatility_20d": round(vol_20d, 2),
            "top3_concentration": round(top3, 1),
            "ma_trend": ma_trend,
            "ret_5d": round(ret_5d, 2),
            "ret_30d": round(ret_30d, 2),
            "holds_list": [f"{h.get('name','')} {h.get('ratio',0)}%" for h in holds[:5]],
        }

    def risk_check(self, funds_data):
        if not self.api_key:
            return "API key 未配置"
        indicators = [self._calc_indicators(f) for f in funds_data]
        data_text = "\n".join([f"基金: {d['name']}\n估值: {d['estimate_value']} 今日: {d['today_change']}%\n回撤: {d['dd_30d']}% 波动率: {d['volatility_20d']}%\n集中度: {d['top3_concentration']}% 趋势: {d['ma_trend']}\n重仓: {', '.join(d['holds_list'])}" for d in indicators])
        system = AI_ANALYSIS_PROMPT.format(knowledge_base=FUND_RISK_RULES + "\n\n" + OPERATION_ADVICE)
        user = "请分析以下基金的风险等级并给出操作建议：\n\n" + data_text
        return self.call_api(system, user, 800, model='deepseek-v4-pro')

    def market_analysis(self, index_data, news_data):
        if not self.api_key:
            return "API key 未配置"
        idx_text = ""
        if index_data:
            idx = index_data[0] if isinstance(index_data, list) else index_data
            if idx and "error" not in idx:
                idx_text = f"指数: {idx.get('name','')} {idx.get('price','')} 涨跌{idx.get('change_pct','')}%"
        news_text = "\n".join([f"- {n.get('title', '')} [{n.get('source', '')}]" for n in (news_data or [])[:10]])
        system = AI_ANALYSIS_PROMPT.format(knowledge_base=MARKET_RULES)
        user = f"当前市场数据:\n{idx_text}\n\n新闻:\n{news_text}\n\n请判断市场情绪和板块方向。"
        return self.call_api(system, user, 600, model='deepseek-v4-pro')

    def daily_report(self, funds_data, index_data, news_data):
        return {"risk": self.risk_check(funds_data), "market": self.market_analysis(index_data, news_data)}

    def news_driven_recommend(self, news_data, index_data, funds_data=None, extra_context=""):
        if not self.api_key:
            return "API key 未配置"
        news_lines = []
        for n in (news_data or [])[:15]:
            news_lines.append(f"- {n.get('title','')}")
        holding_lines = []
        dd_lines = []
        if funds_data:
            for fd in funds_data:
                ind = self._calc_indicators(fd)
                holding_lines.append(f"{ind['name']}: 今日{ind['today_change']}%, 近5日{ind['ret_5d']}%, 30日回撤{ind['dd_30d']}%")
                if abs(ind['dd_30d']) > 5:
                    dd_lines.append(f"{ind['name']}：近30日回撤已达{ind['dd_30d']}%（超预警线）")
        idx_text = ""
        if index_data:
            idx = index_data[0] if isinstance(index_data, list) else index_data
            if idx and "error" not in idx:
                idx_text = f"沪深300: {idx.get('price','')} ({idx.get('change_pct','')}%)"
        news_block = "\n".join(news_lines)
        holding_block = "\n".join(holding_lines) if holding_lines else "（无已持仓数据）"
        dd_block = "\n".join(dd_lines) if dd_lines else "（无异常）"
        system_prompt = f"你是一个专业的A股基金分析管家。\n{NEWS_DRIVEN_RULES}\n分析要求：\n1. 先把每条新闻映射到具体板块\n2. 计算每个板块今日情绪得分（利好+1，利空-1，中性0）\n3. 排除今日已经大涨的板块（避免追高）\n4. 结合已持仓基金的回撤状态，判断是否应补仓/观望/减仓\n5. 给出今日值得关注的3-5只基金，含推荐理由和风险提示\n6. 禁止推荐今日已经大涨>3%的板块对应基金\n7. 禁止使用模糊词汇，必须给出确定性结论"
        user_prompt = f"## 今日市场\n{idx_text}\n## 已持仓基金\n{holding_block}\n## 回撤预警\n{dd_block}{extra_context}\n## 今日重要新闻\n{news_block}\n请按规则分析，输出格式：\n【今日热点板块】\n板块 | 利好/利空 | 催化剂新闻 | 是否已大涨\n\n【今日值得关注的基金】\n基金名称 | 对应板块 | 推荐理由 | 风险提示\n\n【已持仓基金操作建议】\n基金名称 | 建议(持有/加仓/减仓/观望) | 依据\n\n【总结】一句话今日策略"
        return self.call_api(system_prompt, user_prompt, max_tokens=1200, model='deepseek-v4-pro')
