from typing import Any, Dict, TypeVar

from elasticsearch import AsyncElasticsearch, NotFoundError

T = TypeVar("T")


class ElasticWrapper:
    def __init__(self, elastic: AsyncElasticsearch):
        self.elastic = elastic

    async def get_by_id(self, id: str, index: str, model: type[T]):
        try:
            doc = await self.elastic.get(index=index, id=id)
        except NotFoundError:
            return None
        return model(**doc["_source"])

    async def search(self, body: Dict[str, Any], index: str, model: type[T]):
        docs = await self.elastic.search(index=index, body=body)

        sources = docs["hits"]["hits"]

        if sources:
            return [model(**source["_source"]) for source in sources]

        return None

    async def close(self):
        await self.elastic.close()


elastic_wrapper: ElasticWrapper | None = None


# Функция понадобится при внедрении зависимостей
async def get_elastic() -> ElasticWrapper:
    return elastic_wrapper
