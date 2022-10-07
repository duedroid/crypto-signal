import aiofiles
import httpx
import rollbar

from core.config import settings


async def save_klines(
    symbol: str,
    timeframe: str,
    end_ts: str,
    date_str: str
):
    try:
        url = f'{settings.BINANCE_FUTURE_URL}/fapi/v1/klines?symbol={symbol}&interval={timeframe}&limit=499&endTime={end_ts}'
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
        async with aiofiles.open(f'data/{timeframe}/{symbol}.txt', mode='w') as f:
            klines = []
            for kline in r.json():
                klines.append(','.join(map(str, kline[:7])))
            await f.write('\n'.join(klines))
    except:
        rollbar.report_exc_info(extra_data={
            'symbol': symbol,
            'timeframe': timeframe,
            'date': date_str
        })