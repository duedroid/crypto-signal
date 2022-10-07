from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    SERVER_TOKEN: str
    PROJECT_NAME: str = 'shibot'
    ENVIRONMENT: str
    ROLLBAR_ACCESS_TOKEN: str
    REDIS_ARQ_BROKER: str
    REDIS_CACHE: str
    MONGO_URL: str
    MONGO_DB: str
    BINANCE_FUTURE_URL: str = 'https://fapi.binance.com'
    TELEGRAM_URL: str
    TELEGRAM_CHAT_ID: str
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()