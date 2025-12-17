from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.services.genre import GenreService, get_genre_service

router = APIRouter()


class GenresListResponseItem(BaseModel):
    id: str
    name: str
    description: Optional[str]


@router.get("/", response_model=list[GenresListResponseItem])
async def films_list(
    offset: int = 0,
    limit: int = 100,
    film_service: GenreService = Depends(get_genre_service),
) -> list[GenresListResponseItem]:
    films_list = await film_service.get_genres_list(offset=offset, limit=limit)

    return films_list
