# indicators.py - 技术指标计算

import numpy as np

def calc_ma(prices, window):
    """移动平均线"""
    if len(prices) < window:
        return [None] * len(prices)
    ma = list(np.convolve(prices, np.ones(window)/window, mode="valid"))
    return [None] * (window - 1) + ma

def calc_max_drawdown(prices):
    """最大回撤"""
    if not prices or len(prices) < 2:
        return 0
    peak = prices[0]
    max_dd = 0
    for p in prices:
        if p > peak:
            peak = p
        dd = (peak - p) / peak
        if dd > max_dd:
            max_dd = dd
    return max_dd * 100

def calc_daily_returns(prices):
    """日收益率序列"""
    if len(prices) < 2:
        return []
    return [(prices[i] - prices[i-1]) / prices[i-1] * 100 for i in range(1, len(prices))]

def calc_volatility(prices, window=20):
    """波动率（年化）"""
    rets = calc_daily_returns(prices)
    if len(rets) < window:
        return 0
    return np.std(rets[-window:]) * np.sqrt(252)

def calc_win_rate(prices):
    """胜率：上涨天数/总天数"""
    rets = calc_daily_returns(prices)
    if not rets:
        return 0
    up_days = sum(1 for r in rets if r > 0)
    return up_days / len(rets) * 100

if __name__ == "__main__":
    prices = [100, 101, 102, 101, 100, 99, 98, 99, 100, 101]
    print("MA5:", [round(x,2) if x else None for x in calc_ma(prices, 5)])
    print("最大回撤:", round(calc_max_drawdown(prices), 2), "%")
    print("年化波动率:", round(calc_volatility(prices, 5), 2))
    print("胜率:", round(calc_win_rate(prices), 1), "%")
