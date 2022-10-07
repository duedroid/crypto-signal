import numpy as np
import orjson
import rollbar
from talib import EMA, RSI

from core.redis import redis_client


async def calculate_strategy_2(symbol: str, date_str: str):
    # 3 EMA + RSI - 4H
    try:
        klines = np.loadtxt(f'data/4h/{symbol}.txt', delimiter=',')
        prices = np.array([kline[4] for kline in klines]) * (10 ** 5)

        fast_ema = EMA(prices, timeperiod=20)
        mid_ema = EMA(prices, timeperiod=50)
        slow_ema = EMA(prices, timeperiod=200)
        rsi = RSI(prices, timeperiod=7)
        if np.isnan(rsi[-2]) or \
           np.isnan(fast_ema[-2]) or \
           np.isnan(mid_ema[-2]) or \
           np.isnan(slow_ema[-2]):
            return

        cur_fast = fast_ema[-1] / (10 ** 5)
        cur_mid = mid_ema[-1] / (10 ** 5)
        cur_slow = slow_ema[-1] / (10 ** 5)
        prev_fast = fast_ema[-2] / (10 ** 5)
        prev_mid = mid_ema[-2] / (10 ** 5)
        prev_slow = slow_ema[-2] / (10 ** 5)
        long_condition = (cur_fast > cur_mid > cur_slow) and \
                         (prev_fast > prev_mid > prev_slow) and \
                         (rsi[-1] >= 30) and \
                         (rsi[-2] < 30)
        short_condition = (cur_fast < cur_mid < cur_slow) and \
                          (prev_fast < prev_mid < prev_slow) and \
                          (rsi[-1] <= 70) and \
                          (rsi[-2] > 70) 
        
        if long_condition or short_condition:
            pair = symbol.replace('USDT', '_USDT')
            key = f'signal:strategy_2:{pair}'
            data = {
                'side': 'l' if long_condition else 's',
                'date': date_str
            }
            await redis_client.set(key, orjson.dumps(data))
    except:
        rollbar.report_exc_info(extra_data={
            'symbol': symbol,
            'date': date_str
        })