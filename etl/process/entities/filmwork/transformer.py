from typing import Generator

from process.entities.models import (
    FilmWork,
    FilmWorkESDocPerson,
    FilmWorkESDocRaw,
    FilworkPerson,
)

from utils import coroutine


@coroutine
def transform_movies(
    next: Generator[None, list[FilmWorkESDocRaw], None],
) -> Generator[None, list[FilmWork], None]:

    while filworks := (yield):
        transformed_filworks: list[FilmWorkESDocRaw] = []

        for filwork in filworks:
            transformed_persons = [
                FilworkPerson(
                    person_id=p["person_id"],
                    person_name=p["person_name"],
                    person_role=p["person_role"],
                )
                for p in filwork.persons
            ]

            directors = [p for p in transformed_persons if p.person_role == "director"]
            actors = [p for p in transformed_persons if p.person_role == "actor"]
            writers = [p for p in transformed_persons if p.person_role == "writer"]

            transformed = FilmWorkESDocRaw(
                id=str(filwork.id),
                imdb_rating=filwork.rating,
                genres=[g for g in filwork.genres],
                title=filwork.title,
                description=filwork.description,
                directors_names=[d.person_name for d in directors],
                actors_names=[a.person_name for a in actors],
                writers_names=[w.person_name for w in writers],
                directors=[
                    FilmWorkESDocPerson(id=d.person_id, name=d.person_name)
                    for d in directors
                ],
                actors=[
                    FilmWorkESDocPerson(id=a.person_id, name=a.person_name)
                    for a in actors
                ],
                writers=[
                    FilmWorkESDocPerson(id=w.person_id, name=w.person_name)
                    for w in writers
                ],
                modified=filwork.modified,
            )

            transformed_filworks.append(transformed)

        next.send(transformed_filworks)
