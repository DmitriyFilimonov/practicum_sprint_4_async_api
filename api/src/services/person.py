from src.db.redis import get_redis
from fastapi import Depends
from functools import lru_cache
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError

from src.models.person import Person
from src.db.elastic import PERSONS_ES_INDEX, get_elastic

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_person(self, id: str):
        person = await self._get_person_from_cache(id=id)

        if person:
            return person

        person = await self._get_person_from_elastic(id=id)

        await self._put_person_to_cache(person)

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

    async def _put_person_to_cache(self, person: Person):
        await self.redis.set(person.id, person.json(), PERSON_CACHE_EXPIRE_IN_SECONDS)

    async def _get_person_from_cache(self, id: str):
        person = await self.redis.get(id)

        if person:
            return Person.parse_raw(person)

        return None


@lru_cache()
def get_person_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
