from fastapi import Query
from pydantic import BaseModel


class Pagination(BaseModel):
    page_number: int = Query(0, ge=0)
    page_size: int = Query(100, ge=1, le=1000)

    @property
    def offset(self) -> int:
        return self.page_number * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


def get_pagination(
    page_number: int = Query(0, ge=0),
    page_size: int = Query(100, ge=1, le=1000),
) -> Pagination:
    return Pagination(page_number=page_number, page_size=page_size)
