from src.models.pagination import Pagination, get_pagination

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.services.genre import GenreService, get_genre_service

router = APIRouter()


class GenresListResponseItem(BaseModel):
    id: str
    name: str
    description: Optional[str]


@router.get("/{id}", response_model=GenresListResponseItem)
async def genre(
    id: str,
    genre_service: GenreService = Depends(get_genre_service),
) -> GenresListResponseItem:
    genre = await genre_service.get_genre(id=id)

    return genre


@router.get("/", response_model=list[GenresListResponseItem])
async def genres_list(
    pagination: Pagination = Depends(get_pagination),
    genre_service: GenreService = Depends(get_genre_service),
) -> list[GenresListResponseItem]:
    films_list = await genre_service.get_genres_list(
        offset=pagination.offset, limit=pagination.limit
    )

    return films_list
