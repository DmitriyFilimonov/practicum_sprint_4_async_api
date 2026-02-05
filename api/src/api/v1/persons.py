from http import HTTPStatus
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.api.v1.models import NotFoundRes
from src.services.person import PersonService, get_person_service
from src.services.film import FilmService, get_film_service
from src.models.pagination import Pagination, get_pagination

router = APIRouter()


class PersonDetailsResponseFilm(BaseModel):
    uuid: str
    roles: list[str]


class PersonDetailsResponseItem(BaseModel):
    uuid: str
    full_name: str
    films: list[PersonDetailsResponseFilm]


@router.get("/search", response_model=list[PersonDetailsResponseItem])
async def person_details(
    query: Optional[str] = Query(default=None),
    pagination: Pagination = Depends(get_pagination),
    person_service: PersonService = Depends(get_person_service),
) -> list[PersonDetailsResponseItem]:
    persons = await person_service.get_persons_list(
        query=query, offset=pagination.offset, limit=pagination.limit
    )

    return [
        PersonDetailsResponseItem(
            uuid=person.id,
            full_name=person.name,
            films=[
                PersonDetailsResponseFilm(uuid=f.id, roles=f.roles)
                for f in person.films
            ],
        )
        for person in persons
    ]


@router.get(
    "/{id}",
    response_model=PersonDetailsResponseItem,
    responses={404: {"model": NotFoundRes}},
)
async def person_details(
    id: UUID, person_service: PersonService = Depends(get_person_service)
) -> PersonDetailsResponseItem:
    person = await person_service.get_person(id=id)

    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="person not found")

    return PersonDetailsResponseItem(
        uuid=person.id,
        full_name=person.name,
        films=[
            PersonDetailsResponseFilm(uuid=f.id, roles=f.roles) for f in person.films
        ],
    )


class PersonFilmsResponseItem(BaseModel):
    uuid: str
    title: str
    imdb_rating: float


@router.get("/{id}/films", response_model=list[PersonFilmsResponseItem])
async def person_films(
    id: UUID,
    pagination: Pagination = Depends(get_pagination),
    person_service: PersonService = Depends(get_person_service),
    films_service: FilmService = Depends(get_film_service),
) -> list[PersonFilmsResponseItem]:
    person = await person_service.get_person(id=id)

    if person and person.films:
        films_ids = [film.id for film in person.films]

        if len(films_ids):
            films = await films_service.get_films_list(
                id=films_ids, offset=pagination.offset, limit=pagination.limit
            )

            if films and len(films):
                return [
                    PersonFilmsResponseItem(
                        uuid=f.id, title=f.title, imdb_rating=f.imdb_rating
                    )
                    for f in films
                ]

    return []
