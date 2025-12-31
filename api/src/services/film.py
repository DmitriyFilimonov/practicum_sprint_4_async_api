from functools import lru_cache
import json
from typing import Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from src.models.sort import map_sorting
from src.db.elastic import MOVIES_ES_INDEX, get_elastic
from src.db.redis import get_redis
from src.models.film import Film

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    # get_by_id возвращает объект фильма. Он опционален, так как фильм может отсутствовать в базе
    async def get_by_id(self, film_id: str) -> Optional[Film]:
        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        film = await self._film_from_cache(film_id)
        if not film:
            # Если фильма нет в кеше, то ищем его в Elasticsearch
            film = await self._get_film_from_elastic(film_id)
            if not film:
                # Если он отсутствует в Elasticsearch, значит, фильма вообще нет в базе
                return None
            # Сохраняем фильм в кеш
            await self._put_film_to_cache(film)

        return film

    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        try:
            doc = await self.elastic.get(
                index=MOVIES_ES_INDEX,
                id=film_id,
            )
        except NotFoundError:
            return None
        return Film(**doc["_source"])

    async def _film_from_cache(self, film_id: str) -> Optional[Film]:
        # Пытаемся получить данные о фильме из кеша, используя команду get
        # https://redis.io/commands/get/
        data = await self.redis.get(film_id)
        if not data:
            return None

        # pydantic предоставляет удобное API для создания объекта моделей из json
        film = Film.parse_raw(data)
        return film

    async def _put_film_to_cache(self, film: Film):
        # Сохраняем данные о фильме, используя команду set
        # Выставляем время жизни кеша — 5 минут
        # https://redis.io/commands/set/
        # pydantic позволяет сериализовать модель в json
        await self.redis.set(film.id, film.json(), FILM_CACHE_EXPIRE_IN_SECONDS)

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
            index=MOVIES_ES_INDEX, body=body
        )

        sources = films_list_from_elastic["hits"]["hits"]

        return [Film(**source["_source"]) for source in sources]

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
        key_raw = {
            "genres": genres,
            "exclude_id": exclude_id,
            "sort": sort,
            "offset": offset,
            "limit": limit,
            "query": query,
            "id": id,
        }

        key = json.dumps(key_raw, sort_keys=True)
        data = json.dumps([film.dict() for film in films_list], sort_keys=True)

        await self.redis.set(key, data, FILM_CACHE_EXPIRE_IN_SECONDS)

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
        key_raw = {
            # UUID не сериализуется в JSON?
            "genres": [str(g) for g in genres] if genres else None,
            "exclude_id": exclude_id,
            "sort": sort,
            "offset": offset,
            "limit": limit,
            "query": query,
            "id": id,
        }

        key = json.dumps(key_raw, sort_keys=True)

        result_raw = await self.redis.get(key)

        if result_raw:
            result_deserialized = json.loads(result_raw)

            films_list_slice = [Film(**item) for item in result_deserialized]

            return films_list_slice

        return None


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
