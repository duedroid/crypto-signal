import rollbar
from arq import cron

from core.arq import arq_redis_settings
from core.config import settings
from tasks import TASKS
from tasks.signal import binance_future_signal_4h,  binance_future_signal_1d


async def startup(ctx: dict):
    rollbar.init(
        settings.ROLLBAR_ACCESS_TOKEN,
        environment=settings.ENVIRONMENT,
        handler='async',
    )


class WorkerSettings:
    cron_jobs = [
        cron(binance_future_signal_4h, hour={0, 4, 8, 12, 16, 20}, minute=0),
        cron(binance_future_signal_1d, hour=0, minute=0),
    ]
    functions = TASKS
    redis_settings = arq_redis_settings
    on_startup = startup
    keep_result = 60