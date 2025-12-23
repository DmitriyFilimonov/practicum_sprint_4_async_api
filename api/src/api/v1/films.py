from typing import Optional
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.services.film import FilmService, get_film_service

router = APIRouter()


class FilmDetailResponsePerson(BaseModel):
    id: str
    name: str


class FilmDetailsResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    directors_names: list[str]
    actors_names: list[str]
    writers_names: list[str]
    directors: list[FilmDetailResponsePerson]
    actors: list[FilmDetailResponsePerson]
    writers: list[FilmDetailResponsePerson]


@router.get("/{film_id}", response_model=FilmDetailsResponse)
async def film_details(
    film_id: str, film_service: FilmService = Depends(get_film_service)
) -> FilmDetailsResponse:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

    return FilmDetailsResponse(id=film.id, title=film.title)


class FilmListItemResponse(BaseModel):
    uuid: str
    title: str
    imdb_rating: float


@router.get("/", response_model=list[FilmListItemResponse])
async def films_list(
    sort: Optional[str] = Query(
        None,
    ),
    page_size: int = 50,
    page_number: int = 0,
    film_service: FilmService = Depends(get_film_service),
) -> list[FilmListItemResponse]:
    films_list = await film_service.get_films_list(
        sort=sort, offset=page_number * page_size, limit=page_size
    )

    return [
        FilmListItemResponse(uuid=f.id, title=f.title, imdb_rating=f.imdb_rating)
        for f in films_list
    ]
