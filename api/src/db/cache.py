import abc
import json
from src.core import config
from typing import Any, Type, TypeVar, Optional, List
from redis.asyncio import Redis


# единый интерфейс базы данных с кешем
class CacheDB(abc.ABC):
    @abc.abstractmethod
    async def instantiate_cache_db(self): ...

    @abc.abstractmethod
    async def set_value(
        self, key: str, value: Any, expire_time: Optional[int]
    ) -> None: ...

    @abc.abstractmethod
    async def get_value(self, key: str) -> Any | None: ...

    @abc.abstractmethod
    def create_key(self, key_raw: dict[str, Any]) -> str: ...

    @abc.abstractmethod
    async def close(self): ...


# реализация интерфейса базы данных с кешем, в этом случае с помощью Redis
class RedisCahce(CacheDB):
    def __init__(self) -> None:
        self.redis = Redis(
            host=config.settings.redis_host, port=config.settings.redis_port
        )

    async def instantiate_cache_db(self):
        await self.redis.ping()

        return self.redis

    async def set_value(self, key: str, value: Any, expire_time: Optional[int]) -> None:
        await self.redis.set(key, value, expire_time)

    async def get_value(self, key: str) -> str | None:
        try:
            value = await self.redis.get(key)

            return value.decode()

        except:
            return None

    def create_key(self, key_raw: dict[str, Any]):
        return json.dumps(key_raw, sort_keys=True)

    async def close(self):
        await self.redis.close()


T = TypeVar("T")


# единый интерфейс для работы с кешем, не зависящий от конкретной БД для работы с кешем
class Cache:
    def __init__(self, cache_db: CacheDB):
        self.cache_db = cache_db

    async def init(self):
        return await self.cache_db.instantiate_cache_db()

    async def set_value(self, key: str, value: Any, expire_time: Optional[int]):
        await self.cache_db.set_value(key=key, value=value, expire_time=expire_time)

    async def set_value_by_dict_key(
        self, key_raw: dict, value: Any, expire_time: Optional[int]
    ):
        key = self.cache_db.create_key(key_raw)

        await self.set_value(key=key, value=value, expire_time=expire_time)

    async def get_single_value(self, key: str, model: Type[T]) -> Optional[T]:
        result = await self.cache_db.get_value(key)

        if result:
            return model.parse_raw(result)

        return None

    async def get_list_from_cache(
        self,
        key_raw: dict,
        model: Type[T],
    ) -> Optional[List[T]]:
        key = self.cache_db.create_key(key_raw)

        result_raw = await self.cache_db.get_value(key)

        if not result_raw:
            return None

        data = json.loads(result_raw)

        return [model(**item) for item in data]

    async def get_cache(self):
        return self.cache_db

    async def close(self):
        await self.cache_db.close()


cache: Cache | None


def get_cache():
    return cache
