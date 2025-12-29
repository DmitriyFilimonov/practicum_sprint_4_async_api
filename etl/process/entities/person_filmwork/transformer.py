from typing import Generator

from process.entities.models import (
    PersonFilmwork,
    PersonFilmworkESDocRaw,
)

from utils import coroutine


@coroutine
def transform_persons(
    next: Generator[None, list[PersonFilmworkESDocRaw], None],
) -> Generator[None, list[PersonFilmwork], None]:

    while persons := (yield):
        transformed_persons: list[PersonFilmworkESDocRaw] = []

        for person in persons:
            transformed = PersonFilmworkESDocRaw(
                id=str(person.id),
                name=person.full_name,
                films=person.roles_by_films,
                modified=person.modified,
            )

            transformed_persons.append(transformed)

        next.send(transformed_persons)
