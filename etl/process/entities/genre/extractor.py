from datetime import datetime
from typing import Generator

import psycopg
from process.entities.models import FilmWork, FilmworkGenre, FilmworkPerson
from psycopg.rows import class_row
from settings import settings
from utils import coroutine


@coroutine
def extract_movies_by_genre_modified(
    next: Generator[None, list[FilmWork], None],
) -> Generator[None, datetime, None]:
    with (
        psycopg.connect(
            **settings.get_dsl(), row_factory=class_row(FilmWork)
        ) as connection,
        psycopg.ServerCursor(connection=connection, name="genres_extractor") as cursor,
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
                            'genre_id', g_selection.id,
                            'genre_name', g_selection.name,
                            'modified', g_selection.modified
                        )
                    ) FILTER (WHERE g_selection.id is not null),
                    '[]'
                ) as genres
                FROM content.genre g_filter
                JOIN content.genre_film_work gfw_filter ON gfw_filter.genre_id = g_filter.id
                JOIN content.film_work fw ON fw.id = gfw_filter.film_work_id
                LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
                LEFT JOIN content.person p ON p.id = pfw.person_id

                LEFT JOIN content.genre_film_work gfw_selection ON gfw_selection.film_work_id = fw.id
                LEFT JOIN content.genre g_selection ON g_selection.id = gfw_selection.genre_id

                WHERE g_filter.modified > %s
                GROUP BY fw.id
                ORDER BY MAX(g_filter.modified)
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
