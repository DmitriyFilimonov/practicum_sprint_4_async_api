from enum import Enum

from pydantic import BaseModel


class FilmPerson(BaseModel):
    id: str
    name: str


class FilmGenre(BaseModel):
    id: str
    name: str


class Film(BaseModel):
    id: str
    title: str
    description: str | None
    directors_names: list[str]
    actors_names: list[str]
    writers_names: list[str]
    directors: list[FilmPerson]
    actors: list[FilmPerson]
    writers: list[FilmPerson]
    imdb_rating: float | None
    genres: list[FilmGenre]


class FilmSortableFields(str, Enum):
    rating_asc = "imdb_rating"
    rating_desc = "-imdb_rating"
    title_asc = "title"
    title_desc = "-title"


class FilmDocSortableFields(str, Enum):
    imdb_rating = "imdb_rating"
    title = "title.raw"
