import asyncio
import concurrent.futures

import numpy as np
import httpx
import orjson
import pendulum
from multiprocessing import cpu_count

from core.config import settings
from core.redis import redis_client
from strategy.strategy_1 import sync_calculate_strategy_1
from strategy.strategy_2 import sync_calculate_strategy_2


# async def pure_async(symbols: list, date: pendulum.DateTime):
#     tasks = []
#     for symbol in symbols:
#         tasks.append(calculate_cdc(symbol, date))
#     await asyncio.gather(*tasks)


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


async def send_telegram(strategy: str, strategy_name: str, date: pendulum.DateTime):
    try:
        keys = await redis_client.keys(f'signal:{strategy}:*')
        signal_list = await redis_client.mget(keys)
        message = f'<b>{strategy_name} Signal</b>\n\n'
        short_message = '<b>Short</b>'
        long_message = '<b>Long</b>'
        for key, raw_signal in zip(keys, signal_list):
            signal = orjson.loads(raw_signal)
            signal_date = pendulum.parse(signal['date'])
            if signal_date != date:
                continue

            _, strategy, pair = key.split(':')
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
    except Exception as e:
        print(strategy, strategy_name, date, e)


async def load_data(symbol: str, date: pendulum.DateTime):
    try:
        end_ts =  str(int(date.subtract(hours=4).timestamp() * 1000))
        url = f'{settings.BINANCE_FUTURE_URL}/fapi/v1/klines?symbol={symbol}&interval=4h&limit=499&endTime={end_ts}'
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
        klines = r.json()
        data_list = [[float(kline[1]), float(kline[2]), float(kline[3]), float(kline[4])] for kline in klines]
        data_list = np.array(data_list)
        np.savetxt(f'data/{symbol}.txt', data_list, delimiter=',')
    except:
        pass
    

def sync_load_data(symbol: str, date: pendulum.DateTime):
    asyncio.run(load_data(symbol, date))


async def binance_future_signal():
    symbols = await get_symbols()
    now_start = pendulum.now('UTC').start_of('hour')
    date = now_start.replace(hour=int(now_start.hour / 4) * 4)

    NUM_CORES = cpu_count()
    futures = []
    with concurrent.futures.ProcessPoolExecutor(NUM_CORES) as executor:
        for symbol in symbols:
            new_future = executor.submit(
                sync_load_data,
                symbol=symbol,
                date=date,
            )
            futures.append(new_future)
    concurrent.futures.wait(futures)

    futures = []
    with concurrent.futures.ProcessPoolExecutor(NUM_CORES) as executor:
        for symbol in symbols:
            # strategy_1_future = executor.submit(
            #     sync_calculate_strategy_1, symbol=symbol, date=date,
            # )
            # futures.append(strategy_1_future)
            strategy_2_future = executor.submit(
                sync_calculate_strategy_2, symbol=symbol, date=date,
            )
            futures.append(strategy_2_future)
    concurrent.futures.wait(futures)

    tasks = [
        # send_telegram('strategy_1', 'CDC - 4H', date),
        send_telegram('strategy_2', '3 EMA + RSI - 4H', date)
    ]
    await asyncio.gather(*tasks)