import os
import time

from redis import Redis

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")


if __name__ == "__main__":
    redis_client = Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
    )
    while True:
        if redis_client.ping():
            break
        time.sleep(1)
