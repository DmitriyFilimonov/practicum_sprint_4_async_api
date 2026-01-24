from typing import Any, Dict, Optional, Type, TypeVar
from elasticsearch import AsyncElasticsearch, NotFoundError


T = TypeVar("T")


class ElasticWrapper:
    def __init__(self, elastic: AsyncElasticsearch):
        self.elastic = elastic

    async def get_doc_by_id(self, index: str, id: str, model: Type[T]):
        try:
            doc = await self.elastic.get(index=index, id=id)
        except NotFoundError:
            return None
        return model(**doc["_source"])

    async def search(self, index: str, body: Dict[str, Any], model: Type[T]):
        docs = await self.elastic.search(index=index, body=body)

        sources = docs["hits"]["hits"]

        return [model(**source["_source"]) for source in sources]

    async def close(self):
        self.elastic.close()


elastic_wrapper: Optional[ElasticWrapper] = None


# Функция понадобится при внедрении зависимостей
async def get_elastic() -> ElasticWrapper:
    return elastic_wrapper
