import asyncio
# import concurrent.futures

import httpx
import pendulum
import rollbar
# from multiprocessing import cpu_count


from core.arq import get_arq_pool
from core.config import settings
from core.mongo import db
from tasks.klines import save_klines
from tasks.notification import send_telegram
from tasks.strategy import get_strategy


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
        rollbar.report_exc_info()


async def binance_future_signal(timeframe: str):
    try:
        if timeframe == '4h':
            now_start = pendulum.now('UTC').start_of('hour')
            date = now_start.replace(hour=int(now_start.hour / 4) * 4)
            end_ts =  str(int(date.subtract(hours=4).timestamp() * 1000))
        elif timeframe == '1d':
            date = pendulum.now('UTC').start_of('day')
            end_ts =  str(int(date.subtract(days=1).timestamp() * 1000))

        date_str = date.to_atom_string()
        symbols = await get_symbols()
        tasks = []
        for symbol in symbols:
            tasks.append(save_klines(symbol, timeframe, end_ts, date_str))
        await asyncio.gather(*tasks)

        # futures = []
        # NUM_CORES = cpu_count()
        # with concurrent.futures.ProcessPoolExecutor(NUM_CORES) as executor:
        #     for symbol in symbols:
        #         # strategy_1_future = executor.submit(
        #         #     sync_calculate_strategy_1, symbol=symbol, date_str=date_str,
        #         # )
        #         # futures.append(strategy_1_future)
        #         strategy_2_future = executor.submit(
        #             sync_calculate_strategy_2, symbol=symbol, date_str=date_str,
        #         )
        #         futures.append(strategy_2_future)
        # concurrent.futures.wait(futures)

        arq_redis = await get_arq_pool()
        strategy_list = db['strategy_strategy'].find(
            {'timeframe': timeframe},
            {'_id': 0, 'key': 1, 'name': 1, 'timeframe': 1}
        )
        async for strategy in strategy_list:
            await arq_redis.enqueue_job(
                'calculate_strategy',
                strategy, symbols, date_str
            )
        await arq_redis.close()
    except:
        rollbar.report_exc_info(extra_data={
            'timeframe': timeframe
        })


async def calculate_strategy(
    ctx: dict,
    strategy_data: dict,
    symbols: list,
    date_str: str,
):
    try:
        key = strategy_data['key']
        coro = get_strategy(key)
        tasks = []
        for symbol in symbols:
            tasks.append(coro(symbol, date_str))
        await asyncio.gather(*tasks)

        await send_telegram(key, strategy_data['name'], strategy_data['timeframe'], date_str)
    except:
        rollbar.report_exc_info(extra_data={
            'strategy_data': strategy_data,
            'date_str': date_str
        })


async def binance_future_signal_4h(ctx: dict):
    await binance_future_signal('4h')


async def binance_future_signal_1d(ctx: dict):
    await binance_future_signal('1d')