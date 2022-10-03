from redis import asyncio as aioredis

from core.config import settings


redis_client = aioredis.from_url(
    f'redis://{settings.REDIS_AP_HOST}:6379/{settings.REDIS_AP_DB}',
    decode_responses=True
)