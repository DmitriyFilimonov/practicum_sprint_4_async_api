from typing import Generator

from process.entities.models import (
    GenreFilmwork,
    GenreFilmworkESDocRaw,
)

from utils import coroutine


@coroutine
def transform_genres(
    next: Generator[None, list[GenreFilmworkESDocRaw], None],
) -> Generator[None, list[GenreFilmwork], None]:

    while genres := (yield):
        transformed_genres: list[GenreFilmworkESDocRaw] = []

        for genre in genres:
            transformed = GenreFilmworkESDocRaw(
                id=str(genre.id),
                name=genre.name,
                description=genre.description,
                modified=genre.modified,
            )

            transformed_genres.append(transformed)

        next.send(transformed_genres)
