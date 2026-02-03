from enum import Enum
from pydantic import BaseModel
from typing import Optional


class FilmPerson(BaseModel):
    id: str
    name: str


class FilmGenre(BaseModel):
    id: str
    name: str


class Film(BaseModel):
    id: str
    title: str
    description: Optional[str]
    directors_names: list[str]
    actors_names: list[str]
    writers_names: list[str]
    directors: list[FilmPerson]
    actors: list[FilmPerson]
    writers: list[FilmPerson]
    imdb_rating: Optional[float]
    genres: list[FilmGenre]


class FilmSortableFields(str, Enum):
    rating_asc = "imdb_rating"
    rating_desc = "-imdb_rating"
    title_asc = "title"
    title_desc = "-title"


class FilmDocSortableFields(str, Enum):
    imdb_rating = "imdb_rating"
    title = "title.raw"
