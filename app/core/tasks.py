import asyncio
import concurrent.futures

import numpy as np
import httpx
import orjson
import pendulum
from multiprocessing import cpu_count
from redis import asyncio as aioredis
from talib import EMA

from core.config import settings


redis_client = aioredis.from_url(
    f'redis://{settings.REDIS_AP_HOST}:6379/{settings.REDIS_AP_DB}',
    decode_responses=True
)


async def calculate_cdc(symbol: str, date: pendulum.DateTime):
    try:
        end_ts =  str(int(date.subtract(hours=4).timestamp() * 1000))
        url = f'{settings.BINANCE_FUTURE_URL}/fapi/v1/klines?symbol={symbol}&interval=4h&limit=499&endTime={end_ts}'
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
        klines = r.json()
        prices = np.array([])
        for kline in klines:
            price = (float(kline[1]) + float(kline[2]) + float(kline[3]) + float(kline[4])) / 4
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
            key = f'future_signal:{pair}'
            data = {
                'side': cur_side,
                'date': date.to_atom_string()
            }
            await redis_client.set(key, orjson.dumps(data))
    except Exception as e:
        pass


def sync_calculate_cdc(symbol: str, date: pendulum.DateTime):
    asyncio.run(calculate_cdc(symbol, date))


async def pure_async(symbols: list, date: pendulum.DateTime):
    tasks = []
    for symbol in symbols:
        tasks.append(calculate_cdc(symbol, date))
    await asyncio.gather(*tasks)


async def send_telegram(date: pendulum.DateTime):
    keys = await redis_client.keys('future_signal:*')
    signal_list = await redis_client.mget(keys)
    message = '<b>CDC 4H Signal</b>\n\n'
    short_message = '<b>Short</b>'
    long_message = '<b>Long</b>'
    for key, raw_signal in zip(keys, signal_list):
        signal = orjson.loads(raw_signal)
        signal_date = pendulum.parse(signal['date'])
        if signal_date != date:
            continue

        _, pair = key.split(':')
        pair = pair.replace('_', ' / ')
        if signal['side'] == 's':
            short_message += f'\n{pair}'
        else:
            long_message += f'\n{pair}'
        
    message += short_message
    message += '\n=============\n'
    message += long_message

    updated = date.in_timezone('Asia/Bangkok')
    next_updated = updated.add(hours=4)
    message += f'\n\n<b>updated : {updated.to_datetime_string()}\nnext update : {next_updated.to_datetime_string()}</b>'
    async with httpx.AsyncClient() as client:
        r = await client.post(
            url=settings.TELEGRAM_URL,
            json={
                'chat_id': settings.TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
        )


async def binance_future_signal():
    symbols = await get_symbols()
    now_start = pendulum.now('UTC').start_of('hour')
    date = now_start.replace(hour=int(now_start.hour / 4) * 4)

    futures = []
    NUM_CORES = cpu_count()
    with concurrent.futures.ProcessPoolExecutor(NUM_CORES) as executor:
        for symbol in symbols:
            new_future = executor.submit(
                sync_calculate_cdc,
                symbol=symbol,
                date=date,
            )
            futures.append(new_future)
    concurrent.futures.wait(futures)

    await send_telegram(date)


async def get_symbols():
    try:
        url = f'{settings.BINANCE_FUTURE_URL}/fapi/v1/exchangeInfo'
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
        response = r.json()
        symbols = []
        for data in response['symbols']:
            symbol = data['symbol']
            if symbol.endswith('USDT') and data['status'] == 'TRADING':
                symbols.append(symbol)
        return symbols
    except:
        pass