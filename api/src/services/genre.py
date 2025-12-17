from functools import lru_cache
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from src.db.elastic import GENRES_ES_INDEX, get_elastic
from src.db.redis import get_redis
from src.models.genre import Genre


class GenreService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_genres_list(self, offset: int = 0, limit: int = 100) -> list[Genre]:
        genres_list = await self.get_genres_list_from_elastic(
            offset=offset, limit=limit
        )

        return genres_list

    async def get_genres_list_from_elastic(
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
