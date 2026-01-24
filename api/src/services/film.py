from functools import lru_cache
import json
from typing import Optional
from uuid import UUID

from fastapi import Depends

from src.models.sort import map_sorting
from src.db.elastic import ElasticWrapper, get_elastic
from src.db.cache import Cache, get_cache
from src.models.film import Film

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут

MOVIES_ES_INDEX = "movies"


class FilmService:
    def __init__(self, cache: Cache, elastic: ElasticWrapper):
        self.cache = cache
        self.elastic = elastic

    # get_by_id возвращает объект фильма. Он опционален, так как фильм может отсутствовать в базе
    async def get_by_id(self, film_id: str) -> Optional[Film]:
        film = await self._film_from_cache(film_id)

        if not film:
            film = await self._get_film_from_elastic(film_id)

            if not film:
                return None

            await self._put_film_to_cache(film)

        return film

    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        return await self.elastic.get_doc_by_id(
            index=MOVIES_ES_INDEX, id=film_id, model=Film
        )

    async def _film_from_cache(self, film_id: str) -> Optional[Film]:
        film = await self.cache.get_single_value(key=film_id, model=Film)

        return film

    async def _put_film_to_cache(self, film: Film):
        await self.cache.set_value(
            key=film.id, value=film.json(), expire_time=FILM_CACHE_EXPIRE_IN_SECONDS
        )

    async def get_films_list(
        self,
        genres: Optional[list[UUID]] = None,
        exclude_id: Optional[str] = None,
        sort: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
        query: Optional[str] = None,
        id: Optional[list[str]] = None,
    ) -> list[Film]:
        films_list_cache = await self._get_films_list_slice_from_cache(
            sort=sort,
            offset=offset,
            limit=limit,
            genres=genres,
            exclude_id=exclude_id,
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

        if films_list_es:
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

        return None

    async def _get_films_list_from_elastic(
        self,
        genres: Optional[list[UUID]] = None,
        query: Optional[str] = None,
        exclude_id: Optional[str] = None,
        sort: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
        id: Optional[list[str]] = None,
    ) -> list[Film]:
        body = {
            "from": offset,
            "size": limit,
        }

        must = []
        must_not = []

        if id and len(id):
            must.append({"terms": {"id": id}})

        if query:
            must.append(
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^3", "description"],
                        "type": "best_fields",
                        "operator": "and",
                    }
                }
            )

        if genres:
            must.append(
                {
                    "nested": {
                        "path": "genres",
                        "query": {"terms": {"genres.id": [str(g) for g in genres]}},
                    }
                }
            )

        if exclude_id:
            must_not.append({"term": {"id": exclude_id}})

        if must or must_not:
            body["query"] = {"bool": {}}

            if must:
                body["query"]["bool"]["must"] = must

            if must_not:
                body["query"]["bool"]["must_not"] = must_not

        mapped_sorting = map_sorting(sort)

        if mapped_sorting:
            sort_field, order = mapped_sorting
            body["sort"] = {sort_field: {"order": order}}

        films_list_from_elastic = await self.elastic.search(
            index=MOVIES_ES_INDEX, body=body, model=Film
        )

        return films_list_from_elastic

    async def _put_films_list_slice_to_cache(
        self,
        films_list: list[Film],
        genres: Optional[list[UUID]] = None,
        exclude_id: Optional[str] = None,
        sort: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
        query: Optional[str] = None,
        id: Optional[list[str]] = None,
    ):
        await self.cache.set_value_by_dict_key(
            key_raw={
                "genres": genres,
                "exclude_id": exclude_id,
                "sort": sort,
                "offset": offset,
                "limit": limit,
                "query": query,
                "id": id,
            },
            value=json.dumps([film.dict() for film in films_list], sort_keys=True),
            expire_time=FILM_CACHE_EXPIRE_IN_SECONDS,
        )

    async def _get_films_list_slice_from_cache(
        self,
        genres: Optional[list[UUID]] = None,
        exclude_id: Optional[str] = None,
        sort: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
        query: Optional[str] = None,
        id: Optional[list[str]] = None,
    ):
        films_list_slice = await self.cache.get_list_from_cache(
            key_raw={
                # UUID не сериализуется в JSON?
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
    elastic: ElasticWrapper = Depends(get_elastic),
) -> FilmService:
    return FilmService(cache, elastic)
