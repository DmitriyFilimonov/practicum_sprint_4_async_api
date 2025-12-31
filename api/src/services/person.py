import json
from typing import Optional
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

    async def get_persons_list(
        self,
        query: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ):
        persons = await self._get_persons_from_cache(
            query=query, limit=limit, offset=offset
        )

        if persons:
            return persons

        persons = await self._get_persons_list_from_elastic(
            query=query, offset=offset, limit=limit
        )

        self._put_persons_list_to_cache(
            query=query, limit=limit, offset=offset, persons_list=persons
        )

        return persons

    async def _get_persons_from_cache(
        self,
        query: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ):
        key_raw = {"offset": offset, "limit": limit, "query": query}

        key = json.dumps(key_raw, sort_keys=True)

        result_raw = await self.redis.get(
            key,
        )

        if result_raw:
            result_deserialized = json.loads(result_raw)

            persons = [Person(**item) for item in result_deserialized]

            return persons

        return None

    async def _get_persons_list_from_elastic(
        self,
        query: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ):
        body = {
            "from": offset,
            "size": limit,
        }

        must = []

        if query:
            must.append(
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["name"],
                        "type": "best_fields",
                        "operator": "and",
                    }
                }
            )

        if must:
            body["query"] = {"bool": {}}

            if must:
                body["query"]["bool"]["must"] = must

        persons_from_elastic = await self.elastic.search(
            index=PERSONS_ES_INDEX, body=body
        )

        sources = persons_from_elastic["hits"]["hits"]

        persons = [Person(**source["_source"]) for source in sources]

        return persons

    async def _put_persons_list_to_cache(
        self,
        persons_list: list[Person],
        query: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ):

        key_raw = {
            "offset": offset,
            "limit": limit,
            "query": query,
        }

        key = json.dumps(key_raw, sort_keys=True)
        data = json.dumps([person.dict() for person in persons_list], sort_keys=True)

        await self.redis.set(key, data, PERSON_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_person_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
