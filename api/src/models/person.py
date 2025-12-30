from pydantic import BaseModel


class PersonFilm(BaseModel):
    id: str
    roles: list[str]


class Person(BaseModel):
    id: str
    name: str
    films: list[PersonFilm]
