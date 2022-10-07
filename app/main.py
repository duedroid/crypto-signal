import logging
import os
from datetime import datetime, timezone

import rollbar
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from rollbar.contrib.fastapi import ReporterMiddleware as RollbarMiddleware

from core.arq import get_arq_pool
from core.config import settings
from core.mongo import db
from schemas.strategy import CreateStrategySchema
from utils.auth import server_auth_scheme


logger = logging.getLogger(__name__)

rollbar.init(
    settings.ROLLBAR_ACCESS_TOKEN,
    environment=settings.ENVIRONMENT,
    handler='async',
    include_request_body=True,
)

app = FastAPI(title=settings.PROJECT_NAME)
app.add_middleware(RollbarMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup():
    timeframe_list = ['5m', '15m', '30m', '1h', '4h', '1d']
    for timeframe in timeframe_list:
        directory = os.path.join(os.getcwd(), f'data/{timeframe}')
        if not os.path.exists(directory):
            os.makedirs(directory)


@app.get('/')
async def root_api():
    return {'message': 'ok'}


@app.get('/api/test')
async def test_api(auth: bool = Depends(server_auth_scheme)):
    arq_redis = await get_arq_pool()
    await arq_redis.enqueue_job('binance_future_signal_1d')
    await arq_redis.enqueue_job('binance_future_signal_4h')
    await arq_redis.close()
    return {}


@app.post('/api/strategy')
async def create_strategy_api(
    data: CreateStrategySchema,
    auth: bool = Depends(server_auth_scheme)
):
    data_dict = data.dict()
    data_dict['created_at'] = datetime.now(tz=timezone.utc)
    await db['strategy_strategy'].insert_one(data_dict)
    return {}


@app.get('/accounts', response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(
        'accounts.html',
        {
            'request': request,
            'message': 'test'
        }
    )