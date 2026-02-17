from datetime import datetime
from typing import Callable, Generator

from process.entities.models import (
    FilmWork,
    FilmWorkESDocGenre,
    FilmWorkESDocPerson,
    FilmWorkESDocRaw,
)
from utils import coroutine


def filmwork_modified_extractor(filwork: FilmWork) -> datetime:
    return filwork.modified


def genre_modified_extractor(filworks: FilmWork) -> datetime:
    g_modified_values: list[datetime] = []

    for g in filworks.genres:
        g_modified_values.append(g.modified)

    return max(g_modified_values)


def person_modified_extractor(filwork: FilmWork) -> datetime:
    p_modified_values: list[datetime] = []

    for p in filwork.persons:
        p_modified_values.append(p.modified)

    return max(p_modified_values)


@coroutine
def transform_movies(
    next: Generator[None, list[FilmWorkESDocRaw], None],
    last_modified_getter: Callable[[FilmWork], datetime],
) -> Generator[None, list[FilmWork], None]:

    while filworks := (yield):
        transformed_filworks: list[FilmWorkESDocRaw] = []

        for filwork in filworks:
            directors = [p for p in filwork.persons if p.person_role == "director"]
            actors = [p for p in filwork.persons if p.person_role == "actor"]
            writers = [p for p in filwork.persons if p.person_role == "writer"]

            modified = last_modified_getter(filwork)

            transformed = FilmWorkESDocRaw(
                id=str(filwork.id),
                imdb_rating=filwork.rating,
                genres=[
                    FilmWorkESDocGenre(id=g.genre_id, name=g.genre_name)
                    for g in filwork.genres
                ],
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
                modified=modified,
            )

            transformed_filworks.append(transformed)

        next.send(transformed_filworks)
