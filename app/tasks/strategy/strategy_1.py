import numpy as np
import orjson
import rollbar
from talib import EMA

from core.redis import redis_client


async def calculate_strategy_1(symbol: str, date_str: str):
    # CDC - 1D
    try:
        klines = np.loadtxt(f'data/1d/{symbol}.txt', delimiter=',')
        prices = np.array([kline[4] for kline in klines]) * (10 ** 5)

        fast_ema = EMA(prices, timeperiod=12)
        slow_ema = EMA(prices, timeperiod=26)
        cur_fast = fast_ema[-1] / (10 ** 5)
        cur_slow = slow_ema[-1] / (10 ** 5)
        prev_fast = fast_ema[-2] / (10 ** 5)
        prev_slow = slow_ema[-2] / (10 ** 5)
        if np.isnan(prev_fast) or np.isnan(prev_slow):
            return

        long_condition = (cur_fast > cur_slow) and (prev_fast < prev_slow)
        short_condition = (cur_fast < cur_slow) and (prev_fast > prev_slow)
        if long_condition or short_condition:
            pair = symbol.replace('USDT', '_USDT')
            key = f'signal:strategy_1:{pair}'
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