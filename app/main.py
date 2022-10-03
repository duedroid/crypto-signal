import logging
import os

from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pytz import utc

from core.config import settings
from core.tasks import binance_future_signal


logger = logging.getLogger(__name__)


app = FastAPI(title=settings.PROJECT_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


class Scheduler:
    def start(self):
        logger.info("Starting scheduler service.")
        self.scheduler = AsyncIOScheduler(
            jobstores={
                'default': RedisJobStore(host=settings.REDIS_AP_HOST, db=0)
            },
            timezone=utc
        )
        self.scheduler.add_job(
            binance_future_signal,
            'cron',
            id='binance_future_signal',
            hour='*/4',
            minute=0,
            replace_existing=True
        )
        self.scheduler.start()
    

    def shutdown(self):
        logger.info("Shutdown scheduler service")
        self.scheduler.remove_all_jobs()
        self.scheduler.shutdown()


@app.on_event("startup")
async def startup():
    directory = os.path.join(os.getcwd(), 'data')
    if not os.path.exists(directory):
        os.makedirs(directory)

    app.state.scheduler = Scheduler()
    app.state.scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    app.state.scheduler.shutdown()


@app.get('/')
async def root_api():
    return {'message': 'ok'}


@app.get('/test')
async def root_api():
    return await binance_future_signal()