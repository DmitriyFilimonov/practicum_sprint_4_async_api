import time

from redis.asyncio import Redis

from tests.functional import settings


if __name__ == "__main__":
    redis_client = Redis(
        host=settings.settings.redis_host,
        port=settings.settings.redis_port,
    )
    while True:
        if redis_client.ping():
            break
        time.sleep(1)
