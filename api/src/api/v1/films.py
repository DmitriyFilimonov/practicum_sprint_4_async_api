from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from src.api.v1.models import NotFoundRes
from src.models.pagination import Pagination, get_pagination
from src.services.film import FilmService, FilmSortableFields, get_film_service

router = APIRouter()


class FilmListResponseItem(BaseModel):
    uuid: str
    title: str
    imdb_rating: float | None


@router.get("/search", response_model=list[FilmListResponseItem])
async def search_films(
    query: str = None,
    pagination: Pagination = Depends(get_pagination),
    film_service: FilmService = Depends(get_film_service),
):

    films_search_result = await film_service.get_films_list(
        offset=pagination.offset, limit=pagination.limit, query=query
    )

    return [
        FilmListResponseItem(
            uuid=f.id,
            title=f.title,
            imdb_rating=f.imdb_rating,
        )
        for f in films_search_result
    ]


class FilmDetailResponsePerson(BaseModel):
    id: str
    name: str


class FilmDetailsResponse(BaseModel):
    id: str
    title: str
    description: str | None
    directors_names: list[str]
    actors_names: list[str]
    writers_names: list[str]
    directors: list[FilmDetailResponsePerson]
    actors: list[FilmDetailResponsePerson]
    writers: list[FilmDetailResponsePerson]


@router.get(
    "/{film_id}",
    response_model=FilmDetailsResponse,
    responses={404: {"model": NotFoundRes}},
)
async def film_details(
    film_id: UUID, film_service: FilmService = Depends(get_film_service)
) -> FilmDetailsResponse:
    film = await film_service.get_by_id(film_id)

    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="film not found")

    return FilmDetailsResponse(
        id=film.id,
        title=film.title,
        description=film.description,
        directors_names=film.directors_names,
        actors_names=film.actors_names,
        writers_names=film.writers_names,
        actors=[FilmDetailResponsePerson(
            id=a.id, name=a.name) for a in film.actors],
        directors=[
            FilmDetailResponsePerson(id=d.id, name=d.name) for d in film.directors
        ],
        writers=[FilmDetailResponsePerson(
            id=w.id, name=w.name) for w in film.writers],
    )


@router.get("/{film_id}/similar", response_model=list[FilmListResponseItem])
async def similar_films(
    film_id: UUID,
    sort: str | None = Query(default=None),
    pagination: Pagination = Depends(get_pagination),
    film_service: FilmService = Depends(get_film_service),
):
    film = await film_service.get_by_id(film_id)

    if film:
        similar_films = await film_service.get_films_list(
            sort=sort,
            offset=pagination.offset,
            limit=pagination.limit,
            genres=[g.id for g in film.genres],
            exclude_id=film_id,
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
    genres: list[UUID] | None = Query(default=None),
    sort: FilmSortableFields | None = Query(default=None),
    pagination: Pagination = Depends(get_pagination),
    film_service: FilmService = Depends(get_film_service),
) -> list[FilmListResponseItem]:
    films_list = await film_service.get_films_list(
        sort=sort,
        offset=pagination.offset,
        limit=pagination.limit,
        genres=genres,
    )

    return [
        FilmListResponseItem(
            uuid=f.id,
            title=f.title,
            imdb_rating=f.imdb_rating,
        )
        for f in films_list
    ]
