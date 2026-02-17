import json
from functools import lru_cache
from uuid import UUID

from fastapi import Depends
from src.db.cache import Cache, get_cache
from src.db.domain_storages.elastic.genre import AbstractGenreStorage, get_genre_storage
from src.models.genre import Genre

GANRES_CACHE_EXPIRE_IN_SECONDS = 60 * 20


GENRES_ES_INDEX = "genres"


class GenreService:
    def __init__(self, cache: Cache, storage: AbstractGenreStorage):
        self.cache = cache
        self.storage = storage

    async def get_genre(self, id: UUID):
        genre = await self._get_genre_from_cache(id)

        if genre:
            return genre

        genre = await self._get_genre_from_storage(id)

        if genre:
            await self._put_genre_to_cache(genre)

            return genre

        return None

    async def _put_genre_to_cache(self, genre: Genre):
        await self.cache.set_value(
            key=genre.id, value=genre.json(), expire_time=GANRES_CACHE_EXPIRE_IN_SECONDS
        )

    async def _get_genre_from_storage(self, id: UUID):
        return await self.storage.get_by_id(id=str(id))

    async def _get_genre_from_cache(self, id: UUID):
        genre = await self.cache.get_single_value(key=str(id), model=Genre)

        return genre

    async def get_genres_list(self, offset: int = 0, limit: int = 100) -> list[Genre]:
        genres_list_cache = await self._get_genres_list_from_cache(
            offset=offset, limit=limit
        )

        if genres_list_cache:
            return genres_list_cache

        genres_list_es = await self._get_genres_list_from_storage(
            offset=offset, limit=limit
        )

        if genres_list_es:
            await self._put_genres_to_cache(
                genres_list=genres_list_es, limit=limit, offset=offset
            )

            return genres_list_es

        return []

    async def _put_genres_to_cache(
        self, genres_list: list[Genre], offset: int = 0, limit: int = 100
    ):

        data = json.dumps([genre.dict()
                          for genre in genres_list], sort_keys=True)

        await self.cache.set_value_by_dict_key(
            key_raw={
                "offset": offset,
                "limit": limit,
            },
            value=data,
            expire_time=GANRES_CACHE_EXPIRE_IN_SECONDS,
        )

    async def _get_genres_list_from_cache(self, offset: int = 0, limit: int = 100):
        return await self.cache.get_list_from_cache(
            key_raw={"offset": offset, "limit": limit},
            model=Genre,
        )

    async def _get_genres_list_from_storage(
        self, offset: int = 0, limit: int = 100
    ) -> list[Genre] | None:
        return await self.storage.get_list(offset=offset, limit=limit)


@lru_cache()
def get_genre_service(
    cache: Cache = Depends(get_cache),
    storage: AbstractGenreStorage = Depends(get_genre_storage),
) -> GenreService:
    return GenreService(cache=cache, storage=storage)
