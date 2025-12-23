from typing import Optional
from http import HTTPStatus
from uuid import UUID

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


class FilmListResponseItem(BaseModel):
    uuid: str
    title: str
    imdb_rating: Optional[float]

#TODO: подумать, как исключиться оригинальный фильм из выдачи (обязательно)
# подумать, как можно отсортировать фильмы по степени похожести (необязательно)
@router.get("/{film_id}/similar", response_model=list[FilmListResponseItem])
async def similar_films(
    film_id: str,
    sort: Optional[str] = Query(
        default=None,
    ),
    page_size: int = 50,
    page_number: int = 0,
    film_service: FilmService = Depends(get_film_service),
):
    film = await film_service.get_by_id(film_id)

    if film:
        similar_films = await film_service.get_films_list(
            sort=sort,
            offset=page_number * page_size,
            limit=page_size,
            genres=[g.id for g in film.genres],
        )

        return [
            FilmListResponseItem(
                uuid=f.id,
                title=f.title,
                imdb_rating=f.imdb_rating,
            )
            for f in similar_films
        ]
    
    return []


@router.get("/", response_model=list[FilmListResponseItem])
async def films_list(
    genres: Optional[list[UUID]] = Query(default=None),
    sort: Optional[str] = Query(
        default=None,
    ),
    page_size: int = 50,
    page_number: int = 0,
    film_service: FilmService = Depends(get_film_service),
) -> list[FilmListResponseItem]:
    films_list = await film_service.get_films_list(
        sort=sort, offset=page_number * page_size, limit=page_size, genres=genres
    )

    return [
        FilmListResponseItem(
            uuid=f.id,
            title=f.title,
            imdb_rating=f.imdb_rating,
        )
        for f in films_list
    ]
