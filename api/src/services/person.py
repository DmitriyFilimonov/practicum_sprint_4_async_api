import json
from typing import Optional
from uuid import UUID

from src.db.domain_storages.elastic.person import (
    AbstractPersonStorage,
    get_person_storage,
)

from src.db.cache import Cache, get_cache
from fastapi import Depends
from functools import lru_cache

from src.models.person import Person

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5

PERSONS_ES_INDEX = "persons"


class PersonService:
    def __init__(self, cache: Cache, storage: AbstractPersonStorage):
        self.cache = cache
        self.storage = storage

    async def get_person(self, id: UUID):
        person = await self._get_person_from_cache(id=id)

        if person:
            return person

        person = await self._get_person_from_storage(id=id)

        if person:
            await self._put_person_to_cache(person)

            return person

        return None

    async def _get_person_from_storage(self, id: UUID):
        return await self.storage.get_by_id(id=str(id))

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

        persons = await self._get_persons_list_from_storage(
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

    async def _get_persons_list_from_storage(
        self,
        query: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ):

        return await self.storage.get_list(query=query, offset=offset, limit=limit)

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
    storage: AbstractPersonStorage = Depends(get_person_storage),
) -> PersonService:
    return PersonService(cache=cache, storage=storage)
