import json
from typing import Optional
from uuid import UUID
from src.db.cache import Cache, get_cache
from fastapi import Depends
from functools import lru_cache
from elasticsearch import AsyncElasticsearch, NotFoundError

from src.models.person import Person
from src.db.elastic import get_elastic, ElasticWrapper

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5

PERSONS_ES_INDEX = "persons"


class PersonService:
    def __init__(self, cache: Cache, elastic: ElasticWrapper):
        self.cache = cache
        self.elastic = elastic

    async def get_person(self, id: UUID):
        person = await self._get_person_from_cache(id=id)

        if person:
            return person

        person = await self._get_person_from_elastic(id=id)

        if person:
            await self._put_person_to_cache(person)

            return person

        return None

    async def _get_person_from_elastic(self, id: UUID):
        return await self.elastic.get_doc_by_id(
            index=PERSONS_ES_INDEX, id=str(id), model=Person
        )

    async def _put_person_to_cache(self, person: Person):
        await self.cache.set_value(
            key=person.id,
            value=person.json(),
            expire_time=PERSON_CACHE_EXPIRE_IN_SECONDS,
        )

    async def _get_person_from_cache(self, id: UUID):
        person = await self.cache.get_single_value(key=str(id), model=Person)

        return person

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

        if persons:
            await self._put_persons_list_to_cache(
                query=query, limit=limit, offset=offset, persons_list=persons
            )

            return persons

        return []

    async def _get_persons_from_cache(
        self,
        query: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ):
        return await self.cache.get_list_from_cache(
            key_raw={"offset": offset, "limit": limit, "query": query},
            model=Person,
        )

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

        return await self.elastic.search(
            index=PERSONS_ES_INDEX, body=body, model=Person
        )

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

        data = json.dumps([person.dict() for person in persons_list], sort_keys=True)

        await self.cache.set_value_by_dict_key(
            key_raw=key_raw, value=data, expire_time=PERSON_CACHE_EXPIRE_IN_SECONDS
        )


@lru_cache()
def get_person_service(
    cache: Cache = Depends(get_cache),
    elastic: ElasticWrapper = Depends(get_elastic),
) -> PersonService:
    return PersonService(cache, elastic)
