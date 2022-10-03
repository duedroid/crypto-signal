import asyncio

import numpy as np
import orjson
import pendulum
from talib import EMA

from core.redis import redis_client


async def calculate_strategy_1(symbol: str, date: pendulum.DateTime):
    # CDC - 4H
    try:
        klines = np.loadtxt(f'data/{symbol}.txt', delimiter=',')
        prices = np.array([])
        for kline in klines:
            price = (float(kline[0]) + float(kline[1]) + float(kline[2]) + float(kline[3])) / 4
            prices = np.append(prices, [price])

        fast_ema = EMA(prices * (10 ** 5), timeperiod=12)
        slow_ema = EMA(prices * (10 ** 5), timeperiod=26)
        cur_fast = fast_ema[-1] / (10 ** 5)
        cur_slow = slow_ema[-1] / (10 ** 5)
        prev_fast = fast_ema[-2] / (10 ** 5)
        prev_slow = slow_ema[-2] / (10 ** 5)
        if np.isnan(prev_fast) or np.isnan(prev_slow):
            return

        cur_side = 'l' if cur_fast > cur_slow else 's'
        prev_side = 'l' if prev_fast > prev_slow else 's'
        if cur_side != prev_side:
            pair = symbol.replace('USDT', '_USDT')
            key = f'signal:strategy_1:{pair}'
            data = {
                'side': cur_side,
                'date': date.to_atom_string()
            }
            await redis_client.set(key, orjson.dumps(data))
    except Exception as e:
        print('strategy_1', symbol, e)


def sync_calculate_strategy_1(symbol: str, date: pendulum.DateTime):
    asyncio.run(calculate_strategy_1(symbol, date))