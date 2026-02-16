from typing import Any, Dict, Generic, List, TypeVar


from src.db.elastic import ElasticWrapper


T = TypeVar("T")


class CommonStorage(Generic[T]):
    def __init__(
        self,
        elastic: ElasticWrapper,
        index: str,
        model: type[T],
    ):
        self.elastic = elastic
        self.index = index
        self.model = model

    async def get_by_id(self, id: str) -> T | None:
        return await self.elastic.get_by_id(index=self.index, id=id, model=self.model)

    async def get_list(self, body: Dict[str, Any]) -> List[T] | None:
        return await self.elastic.search(index=self.index, body=body, model=self.model)
