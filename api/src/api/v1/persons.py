from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.services.person import PersonService, get_person_service

router = APIRouter()


class PersonDetailsResponseFilm(BaseModel):
    uuid: str
    roles: list[str]


class PersonDetailsResponse(BaseModel):
    uuid: str
    full_name: str
    films: list[PersonDetailsResponseFilm]


@router.get("/{id}", response_model=PersonDetailsResponse)
async def film_details(
    id: str, person_service: PersonService = Depends(get_person_service)
) -> PersonDetailsResponse:
    person = await person_service.get_person(id=id)

    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

    return PersonDetailsResponse(
        uuid=person.id,
        full_name=person.name,
        films=[
            PersonDetailsResponseFilm(uuid=f.id, roles=f.roles) for f in person.films
        ],
    )
