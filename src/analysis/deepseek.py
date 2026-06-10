# deepseek.py - DeepSeek AI 分析模块
# 调用 DeepSeek API 做新闻分析和每日研判

import requests
import json
import os

API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-chat"

class DeepSeekAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def analyze_news(self, news_list, fund_name="", stock_names=None):
        """分析新闻对持仓的影响"""
        if not news_list or not self.api_key:
            return None
        
        titles = "\n".join([f"- {n.get("title", "")}" for n in news_list[:10]])
        stock_info = f"，关联股票：{', '.join(stock_names[:5])}" if stock_names else ""
        
        prompt = f"""你是一个专业的基金分析助手。以下是与{fund_name}{stock_info}相关的今日新闻，请分析：
1. 这些新闻整体情绪偏正面还是负面？
2. 哪些新闻最值得关注？简要说明原因。
3. 对基金短期走势有什么潜在影响？

新闻列表：
{titles}

请用中文简短回答，200字以内。"""

        return self._call_api(prompt)

    def daily_summary(self, fund_data, stock_data, news_count):
        """收盘总结"""
        if not self.api_key:
            return None
        
        fund_info = fund_data.get("name", "基金")
        net_change = fund_data.get("change_pct", "N/A")
        estimate_change = fund_data.get("estimate_change_pct", "N/A")
        
        stock_summary = ""
        if stock_data:
            top_move = max(stock_data, key=lambda s: abs(s.get("change_pct", 0)))
            stock_summary = f"重仓股中 {top_move.get('name','')} 变动最大({top_move.get('change_pct',0)}%)"

        prompt = f"""你是一个专业的基金分析助手，根据以下数据生成今日基金研判：

基金：{fund_info}
净值涨幅：{net_change}%
盘中估值涨幅：{estimate_change}%
{stock_summary}
今日相关新闻：{news_count}条

请生成一段200字以内的今日研判："""
        
        return self._call_api(prompt)

    def _call_api(self, prompt):
        """调用 DeepSeek API"""
        try:
            payload = {
                "model": DEFAULT_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一个专业的中国基金分析助手，擅长解读基金和股票市场信息。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }
            r = requests.post(API_URL, headers=self.headers, json=payload, timeout=30)
            r.raise_for_status()
            result = r.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[分析请求失败: {str(e)}]"

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    try:
        with open("../config.json") as f:
            cfg = json.load(f)
        api_key = cfg.get("deepseek_api_key", "")
        if api_key:
            ai = DeepSeekAnalyzer(api_key)
            # 测试新闻分析
            result = ai.analyze_news(
                [{"title": "A股三大指数集体收涨 消费板块走强"}],
                "测试基金"
            )
            print("Analysis:", result)
        else:
            print("SKIP: no API key set")
    except FileNotFoundError:
        print("SKIP: config.json not found (running standalone)")
