from redis import asyncio as aioredis

from core.config import settings


redis_client = aioredis.from_url(settings.REDIS_ARQ_BROKER, decode_responses=True)