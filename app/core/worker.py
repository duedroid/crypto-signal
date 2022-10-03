from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc

from core.config import settings


scheduler = AsyncIOScheduler(
    jobstores={
        'default': RedisJobStore(host=settings.REDIS_AP_HOST, db=0)
    },
    timezone=utc
)