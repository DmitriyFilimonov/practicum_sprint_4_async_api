import psycopg
from process.entities.models import FilmWork, FilmworkGenre, FilmworkPerson
from psycopg.rows import class_row
from settings import settings
from datetime import datetime
from typing import Generator

from utils import coroutine
from process.entities.models import FilmWork


@coroutine
def extract_movies_by_modified(
    next: Generator[None, list[FilmWork], None],
) -> Generator[None, datetime, None]:

    with (
        psycopg.connect(
            **settings.get_dsl(), row_factory=class_row(FilmWork)
        ) as connection,
        psycopg.ServerCursor(connection=connection, name="movies_extractor") as cursor,
    ):
        while last_updated := (yield):
            cursor.execute(
                """
                SELECT
                fw.id,
                fw.title,
                fw.description,
                fw.rating,
                fw.type,
                fw.created,
                fw.modified,
                COALESCE (
                    json_agg(
                        DISTINCT jsonb_build_object(
                            'person_role', pfw.role,
                            'person_id', p.id,
                            'person_name', p.full_name,
                            'modified', p.modified
                        )
                    ) FILTER (WHERE p.id is not null),
                    '[]'
                ) as persons,
                COALESCE (
                    json_agg(
                        DISTINCT jsonb_build_object(
                            'genre_name', g.name,
                            'modified', g.modified
                        )
                    ) FILTER (WHERE g.id is not null),
                    '[]'
                ) as genres
                FROM content.film_work fw
                LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
                LEFT JOIN content.person p ON p.id = pfw.person_id
                LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
                LEFT JOIN content.genre g ON g.id = gfw.genre_id
                WHERE fw.modified > %s
                GROUP BY fw.id
                ORDER BY fw.modified
                LIMIT 100;
                """,
                (last_updated,),
            )

            while results := cursor.fetchmany(size=100):
                next.send(
                    FilmWork(
                        id=r.id,
                        title=r.title,
                        description=r.description,
                        rating=r.rating,
                        type=r.type,
                        created=r.created,
                        modified=r.modified,
                        persons=[FilmworkPerson(**p) for p in r.persons],
                        genres=[FilmworkGenre(**g) for g in r.genres],
                    )
                    for r in results
                )
