from typing import Protocol
from uuid import UUID

from fastapi import Depends


from src.db.elastic import ElasticWrapper, get_elastic
from src.db.domain_storages.elastic.common import CommonStorage
from src.models.sort import map_sorting


from src.models.film import Film, FilmDocSortableFields, FilmSortableFields


MOVIES_ES_INDEX = "movies"


class AbstractFilmStorage(Protocol):
    async def get_by_id(self, id: str) -> Film | None: ...

    async def get_list(
        self,
        genres: list[UUID] | None = None,
        query: str | None = None,
        exclude_id: str | None = None,
        sort: FilmSortableFields | None = None,
        offset: int = 0,
        limit: int = 100,
        id: list[str] | None = None,
    ) -> list[Film] | None: ...


class ElasticFilmStorage(CommonStorage, AbstractFilmStorage):
    def __init__(self, elastic: ElasticWrapper):
        super().__init__(elastic=elastic, index=MOVIES_ES_INDEX, model=Film)

    async def get_list(
        self,
        genres=None,
        query=None,
        exclude_id=None,
        sort=None,
        offset=0,
        limit=100,
        id=None,
    ):
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
                        "operator": "or",
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

        mapped_sorting = map_sorting(sort=sort, sortable_fields=FilmDocSortableFields)

        if mapped_sorting:
            sort_field, order = mapped_sorting
            body["sort"] = {sort_field: {"order": order}}

        films_list_from_elastic = await super().get_list(body=body)

        return films_list_from_elastic


def get_film_storage(
    elastic: ElasticWrapper = Depends(get_elastic),
):
    return ElasticFilmStorage(elastic=elastic)
