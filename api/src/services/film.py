from functools import lru_cache
from typing import Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends, Query
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
        genre: Optional[UUID],
        sort: Optional[str] = Query(
            None,
        ),
        offset: int = 0,
        limit: int = 100,
    ) -> list[Film]:

        films_list = await self._get_films_list_from_elastic(
            sort=sort, offset=offset, limit=limit, genre=genre
        )

        return films_list

    async def _get_films_list_from_elastic(
        self,
        genre: Optional[UUID],
        sort: Optional[str] = Query(
            None,
        ),
        offset: int = 0,
        limit: int = 100,
    ) -> list[Film]:
        body = {
            "from": offset,
            "size": limit,
        }

        mapped_sorting = map_sorting(sort)

        body["query"] = {
            "nested": {"path": "genres", "query": {"term": {"genres.id": str(genre)}}}
        }

        if mapped_sorting:
            sort_field, order = mapped_sorting
            body["sort"] = {sort_field: {"order": order}}

        films_list_from_elastic = await self.elastic.search(
            index=MOVIES_ES_INDEX, body=body
        )

        sources = films_list_from_elastic["hits"]["hits"]

        return [Film(**source["_source"]) for source in sources]


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
