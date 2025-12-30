from src.db.redis import get_redis
from fastapi import Depends
from functools import lru_cache
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError

from src.models.person import Person
from src.db.elastic import PERSONS_ES_INDEX, get_elastic


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_person(self, id: str):
        person = await self._get_person_from_elastic(id=id)

        return person

    async def _get_person_from_elastic(self, id: str):
        try:
            doc = await self.elastic.get(
                index=PERSONS_ES_INDEX,
                id=id,
            )
        except NotFoundError:
            return None
        return Person(**doc["_source"])


@lru_cache()
def get_person_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
