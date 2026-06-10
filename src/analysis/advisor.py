# advisor.py - AI 管家：基于技术知识库的基金分析
import json
import requests
import numpy as np
from .knowledge import (
    FUND_RISK_RULES, MARKET_RULES, FUND_SELECTION_RULES,
    OPERATION_ADVICE, AI_ANALYSIS_PROMPT
)


class AIAdvisor:
    def __init__(self, api_key, model="deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.deepseek.com/chat/completions"

    def call_api(self, system_prompt, user_prompt, max_tokens=800):
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
                    "model": self.model,
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

    # ======== 数学指标计算 ========
    def _calc_indicators(self, fund_data):
        est = fund_data.get("est", {})
        hist = fund_data.get("hist", [])
        holds = fund_data.get("holdings", [])

        # 日收益率序列
        daily_chgs = []
        for h in hist[-30:]:
            try:
                v = float(h.get("daily_change_pct", 0))
                daily_chgs.append(v)
            except:
                daily_chgs.append(0)

        # 净值序列
        net_values = []
        for h in hist[-30:]:
            try:
                v = float(h.get("net_value", 0))
                if v > 0:
                    net_values.append(v)
            except:
                pass

        # 30日最大回撤
        dd_30d = 0
        if net_values:
            peak = net_values[0]
            for v in net_values:
                if v > peak:
                    peak = v
                d = (peak - v) / peak * 100
                if d > dd_30d:
                    dd_30d = d

        # 20日年化波动率
        vol_20d = np.std(daily_chgs[-20:]) * np.sqrt(252) if len(daily_chgs) >= 5 else 0

        # 前3持仓集中度
        top3 = sum(h.get("ratio", 0) for h in holds[:3])

        # 均线判断
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

        # 近5日收益
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

    # ======== 风险分析 ========
    def risk_check(self, funds_data):
        if not self.api_key:
            return "API key 未配置"

        indicators = [self._calc_indicators(f) for f in funds_data]
        data_text = "\n".join([
            f"""
基金: {d['name']}
估值: {d['estimate_value']}, 今日涨跌: {d['today_change']}%
近5日: {d['ret_5d']}%, 近30日: {d['ret_30d']}%
30日最大回撤: {d['dd_30d']}%, 20日波动率: {d['volatility_20d']}%
前3持仓集中度: {d['top3_concentration']}%
均线状态: {d['ma_trend']}
重仓股: {', '.join(d['holds_list'])}
"""
            for d in indicators
        ])

        system = AI_ANALYSIS_PROMPT.format(knowledge_base=FUND_RISK_RULES + "\n\n" + OPERATION_ADVICE)
        user = "请分析以下基金的风险等级并给出操作建议：\n\n" + data_text
        return self.call_api(system, user, 800)

    # ======== 市场分析 ========
    def market_analysis(self, index_data, news_data):
        if not self.api_key:
            return "API key 未配置"

        idx_text = ""
        if index_data:
            idx = index_data[0] if isinstance(index_data, list) else index_data
            if idx and "error" not in idx:
                idx_text = f"指数: {idx.get('name','')} {idx.get('price','')} 涨跌{idx.get('change_pct','')}%"

        news_text = "\n".join([
            f"- {n.get('title', '')} [{n.get('source', '')}]"
            for n in (news_data or [])[:10]
        ])

        system = AI_ANALYSIS_PROMPT.format(knowledge_base=MARKET_RULES)
        user = f"当前市场数据:\n{idx_text}\n\n新闻:\n{news_text}\n\n请判断市场情绪和板块方向。"
        return self.call_api(system, user, 600)

    # ======== 综合日报 ========
    def daily_report(self, funds_data, index_data, news_data):
        return {
            "risk": self.risk_check(funds_data),
            "market": self.market_analysis(index_data, news_data),
        }
