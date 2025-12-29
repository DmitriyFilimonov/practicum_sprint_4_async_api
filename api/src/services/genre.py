import json
from functools import lru_cache
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from src.db.elastic import GENRES_ES_INDEX, get_elastic
from src.db.redis import get_redis
from src.models.genre import Genre


GANRES_CACHE_EXPIRE_IN_SECONDS = 60 * 20


class GenreService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_genres_list(self, offset: int = 0, limit: int = 100) -> list[Genre]:
        genres_list_cache = await self._get_genres_list_from_cache(
            offset=offset, limit=limit
        )

        if genres_list_cache:
            return genres_list_cache

        genres_list_es = await self._get_genres_list_from_elastic(
            offset=offset, limit=limit
        )

        if genres_list_es:
            await self._put_genres_to_cache(
                genres_list=genres_list_es, limit=limit, offset=offset
            )

            return genres_list_es

        return None

    async def _put_genres_to_cache(
        self, genres_list: list[Genre], offset: int = 0, limit: int = 100
    ):
        key_raw = {
            "offset": offset,
            "limit": limit,
        }

        key = json.dumps(key_raw, sort_keys=True)
        data = json.dumps([genre.dict() for genre in genres_list], sort_keys=True)

        await self.redis.set(key, data, GANRES_CACHE_EXPIRE_IN_SECONDS)

    async def _get_genres_list_from_cache(self, offset: int = 0, limit: int = 100):
        key_raw = {
            "offset": offset,
            "limit": limit,
        }

        key = json.dumps(key_raw, sort_keys=True)

        result_raw = await self.redis.get(
            key,
        )

        if result_raw:
            result_deserialized = json.loads(result_raw)

            genres_list = [Genre(**item) for item in result_deserialized]

            return genres_list

        return None

    async def _get_genres_list_from_elastic(
        self, offset: int = 0, limit: int = 100
    ) -> list[Genre]:
        doc = await self.elastic.search(
            index=GENRES_ES_INDEX, body={"from": offset, "size": limit}
        )

        sources = doc["hits"]["hits"]

        return [Genre(**source["_source"]) for source in sources]


@lru_cache()
def get_genre_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
