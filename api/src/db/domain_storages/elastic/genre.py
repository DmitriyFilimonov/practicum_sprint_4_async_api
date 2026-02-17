from typing import Protocol

from fastapi import Depends
from src.db.domain_storages.elastic.common import CommonStorage
from src.db.elastic import ElasticWrapper, get_elastic
from src.models.genre import Genre

GENRES_ES_INDEX = "genres"


class AbstractGenreStorage(Protocol):
    async def get_by_id(self, id: str) -> Genre | None: ...

    async def get_list(
        self, offset: int = 0, limit: int = 100
    ) -> list[Genre] | None: ...


class ElasticGenreStorage(CommonStorage[Genre], AbstractGenreStorage):
    def __init__(self, elastic: ElasticWrapper):
        super().__init__(elastic=elastic, index=GENRES_ES_INDEX, model=Genre)

    async def get_list(self, offset=0, limit=100):
        return await super().get_list(body={"from": offset, "size": limit})


def get_genre_storage(
    elastic: ElasticWrapper = Depends(get_elastic),
):
    return ElasticGenreStorage(elastic=elastic)
