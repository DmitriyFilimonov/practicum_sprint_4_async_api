import json
from functools import lru_cache
from uuid import UUID

from fastapi import Depends
from src.db.cache import Cache, get_cache
from src.db.domain_storages.elastic.film import (
    AbstractFilmStorage,
    get_film_storage,
)
from src.models.film import Film, FilmSortableFields

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class FilmService:
    def __init__(self, cache: Cache, storage: AbstractFilmStorage):
        self.cache = cache
        self.storage = storage

    # get_by_id возвращает объект фильма.
    # Он опционален, так как фильм может отсутствовать в базе
    async def get_by_id(self, film_id: UUID) -> Film | None:
        film = await self._film_from_cache(film_id)

        if not film:
            film = await self._get_film_from_elastic(film_id)

            if not film:
                return None

            await self._put_film_to_cache(film)

        return film

    async def _get_film_from_elastic(self, film_id: UUID) -> Film | None:
        return await self.storage.get_by_id(id=str(film_id))

    async def _film_from_cache(self, film_id: UUID) -> Film | None:
        film = await self.cache.get_single_value(key=str(film_id), model=Film)

        return film

    async def _put_film_to_cache(self, film: Film):
        await self.cache.set_value(
            key=film.id, value=film.json(), expire_time=FILM_CACHE_EXPIRE_IN_SECONDS
        )

    async def get_films_list(
        self,
        genres: list[UUID] | None = None,
        exclude_id: str | None = None,
        sort: FilmSortableFields | None = None,
        offset: int = 0,
        limit: int = 100,
        query: str | None = None,
        id: list[str] | None = None,
    ) -> list[Film]:
        films_list_cache = await self._get_films_list_slice_from_cache(
            genres=genres,
            exclude_id=exclude_id,
            sort=sort,
            offset=offset,
            limit=limit,
            query=query,
            id=id,
        )

        if films_list_cache:
            return films_list_cache

        films_list_es = await self._get_films_list_from_elastic(
            sort=sort,
            offset=offset,
            limit=limit,
            genres=genres,
            query=query,
            exclude_id=exclude_id,
            id=id,
        )

        if films_list_es and len(films_list_es):
            await self._put_films_list_slice_to_cache(
                films_list=films_list_es,
                exclude_id=exclude_id,
                genres=genres,
                limit=limit,
                offset=offset,
                sort=sort,
                query=query,
                id=id,
            )

            return films_list_es

        return []

    async def _get_films_list_from_elastic(
        self,
        genres: list[UUID] | None = None,
        query: str | None = None,
        exclude_id: str | None = None,
        sort: FilmSortableFields | None = None,
        offset: int = 0,
        limit: int = 100,
        id: list[str] | None = None,
    ):
        return await self.storage.get_list(
            sort=sort,
            offset=offset,
            limit=limit,
            genres=genres,
            query=query,
            exclude_id=exclude_id,
            id=id,
        )

    async def _put_films_list_slice_to_cache(
        self,
        films_list: list[Film],
        genres: list[UUID] | None = None,
        exclude_id: str | None = None,
        sort: str | None = None,
        offset: int = 0,
        limit: int = 100,
        query: str | None = None,
        id: list[str] | None = None,
    ):
        await self.cache.set_value_by_dict_key(
            key_raw={
                "genres": [str(g) for g in genres] if genres else None,
                "exclude_id": exclude_id,
                "sort": sort,
                "offset": offset,
                "limit": limit,
                "query": query,
                "id": id,
            },
            value=json.dumps([film.dict()
                             for film in films_list], sort_keys=True),
            expire_time=FILM_CACHE_EXPIRE_IN_SECONDS,
        )

    async def _get_films_list_slice_from_cache(
        self,
        genres: list[UUID] | None = None,
        exclude_id: str | None = None,
        sort: FilmSortableFields | None = None,
        offset: int = 0,
        limit: int = 100,
        query: str | None = None,
        id: list[str] | None = None,
    ):
        films_list_slice = await self.cache.get_list_from_cache(
            key_raw={
                "genres": [str(g) for g in genres] if genres else None,
                "exclude_id": exclude_id,
                "sort": sort,
                "offset": offset,
                "limit": limit,
                "query": query,
                "id": id,
            },
            model=Film,
        )

        return films_list_slice


@lru_cache()
def get_film_service(
    cache: Cache = Depends(get_cache),
    storage: AbstractFilmStorage = Depends(get_film_storage),
) -> FilmService:
    return FilmService(cache=cache, storage=storage)
