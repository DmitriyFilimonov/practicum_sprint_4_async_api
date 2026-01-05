from src.core import config
from typing import Optional
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError

redis: Optional[Redis] = None

ERRORS = (ConnectionError, TimeoutError)

async def instanciate_redis():
    redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)

    await redis.ping()

    return redis


# Функция понадобится при внедрении зависимостей
async def get_redis() -> Redis:
    return redis
