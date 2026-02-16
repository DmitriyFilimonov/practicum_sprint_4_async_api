from abc import ABC, abstractmethod
from typing import Optional

from fastapi import Depends


from src.db.elastic import ElasticWrapper, get_elastic
from src.db.domain_storages.elastic.common import CommonStorage
from src.models.person import Person


PERSONS_ES_INDEX = "persons"


class AbstractPersonStorage(ABC):
    @abstractmethod
    async def get_by_id(self, id: str) -> Person | None: ...

    @abstractmethod
    async def get_list(
        self, query: Optional[str] = None, offset: int = 0, limit: int = 100
    ) -> list[Person] | None: ...


class ElasticPersonStorage(CommonStorage[Person], AbstractPersonStorage):
    def __init__(self, elastic: ElasticWrapper):
        super().__init__(elastic=elastic, index=PERSONS_ES_INDEX, model=Person)

    async def get_list(self, query=None, offset=0, limit=100):
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

        return await super().get_list(body=body)


def get_person_storage(
    elastic: ElasticWrapper = Depends(get_elastic),
):
    return ElasticPersonStorage(elastic=elastic)
