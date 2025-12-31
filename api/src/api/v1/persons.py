from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.services.person import PersonService, get_person_service
from src.services.film import FilmService, get_film_service

router = APIRouter()


class PersonDetailsResponseFilm(BaseModel):
    uuid: str
    roles: list[str]


class PersonDetailsResponseItem(BaseModel):
    uuid: str
    full_name: str
    films: list[PersonDetailsResponseFilm]


@router.get("/search", response_model=list[PersonDetailsResponseItem])
async def film_details(
    query: str = None,
    page_size: int = 100,
    page_number: int = 0,
    person_service: PersonService = Depends(get_person_service),
) -> list[PersonDetailsResponseItem]:
    persons = await person_service.get_persons_list(
        query=query, limit=page_size, offset=page_number * page_size
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


@router.get("/{id}", response_model=PersonDetailsResponseItem)
async def film_details(
    id: str, person_service: PersonService = Depends(get_person_service)
) -> PersonDetailsResponseItem:
    person = await person_service.get_person(id=id)

    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

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


@router.get("/{id}/film", response_model=list[PersonFilmsResponseItem])
async def person_films(
    id: str,
    page_number: int = 0,
    page_size: int = 100,
    person_service: PersonService = Depends(get_person_service),
    films_service: FilmService = Depends(get_film_service),
) -> list[PersonFilmsResponseItem]:
    person = await person_service.get_person(id=id)

    if person and person.films:
        films_ids = [film.id for film in person.films]

        if len(films_ids):
            films = await films_service.get_films_list(
                id=films_ids, limit=page_size, offset=page_number
            )

            if films and len(films):
                return [
                    PersonFilmsResponseItem(
                        uuid=f.id, title=f.title, imdb_rating=f.imdb_rating
                    )
                    for f in films
                ]

    return []
