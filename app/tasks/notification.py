import httpx
import orjson
import pendulum
import rollbar

from core.config import settings
from core.redis import redis_client


async def send_telegram(
    strategy: str,
    strategy_name: str,
    timeframe: str,
    date_str: str
):
    try:
        date = pendulum.parse(date_str)
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
        if timeframe == '4h':
            next_updated = updated.add(hours=4)
        elif timeframe == '1d':
            next_updated = updated.add(days=1)
        else:
            return

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
    except:
        rollbar.report_exc_info(extra_data={
            'strategy': strategy,
            'strategy_name': strategy_name,
            'date': date.to_atom_string()
        })