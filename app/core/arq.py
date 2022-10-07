from arq import create_pool
from arq.connections import RedisSettings

from core.config import settings


arq_redis_settings = RedisSettings.from_dsn(settings.REDIS_ARQ_BROKER)


async def get_arq_pool():
    return await create_pool(arq_redis_settings)