from src.core import config
from typing import Optional
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError

redis: Optional[Redis] = None

ERRORS = (ConnectionError, TimeoutError)


async def instanciate_redis():
    redis = Redis(host=config.settings.redis_host, port=config.settings.redis_port)

    await redis.ping()

    return redis


# Функция понадобится при внедрении зависимостей
async def get_redis() -> Redis:
    return redis
