from datetime import datetime

import abc
from typing import Any
from redis import Redis
from utils import backoff
import settings
from settings import settings


class BaseStorage(abc.ABC):
    @abc.abstractmethod
    def set_value(self, key: str, value: Any) -> None: ...

    @abc.abstractmethod
    def get_value(self, key: str) -> Any | None: ...


class RemoteStorage(BaseStorage):
    def __init__(self) -> None:
        self.redis = Redis(host=settings.redis_host, port=settings.redis_port)

    def set_value(self, key: str, value: Any) -> None:
        self.redis.set(key, value)

    def get_value(self, key: str) -> str | None:
        try:
            value = self.redis.get(key)

            return value.decode()

        except:
            return None


class State:
    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage

    @backoff(border_sleep_time=60)
    def set_state(self, key: str, value: datetime) -> None:
        self.storage.set_value(key, value.isoformat())

    @backoff(border_sleep_time=60)
    def get_state(self, state_key: str) -> datetime:
        raw_date_time = self.storage.get_value(state_key)

        if raw_date_time == None:
            return datetime.min

        return datetime.fromisoformat(raw_date_time)
