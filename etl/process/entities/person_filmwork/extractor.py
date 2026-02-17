from datetime import datetime
from logging import info
from typing import Generator

import psycopg
from process.entities.models import PersonFilmwork
from psycopg.rows import class_row
from settings import settings
from utils import coroutine


@coroutine
def extract_persons_by_modified(
    next: Generator[None, list[PersonFilmwork], None],
) -> Generator[None, datetime, None]:

    with (
        psycopg.connect(
            **settings.get_dsl(), row_factory=class_row(PersonFilmwork)
        ) as connection,
        psycopg.ServerCursor(
            connection=connection, name="person_filmwork_extractor"
        ) as cursor,
    ):
        while last_updated := (yield):
            cursor.execute(
                """
                SELECT
                p.id,
                p.full_name,
                p.modified,
                json_agg(
                    json_build_object(
                        'id', pfw.film_work_id,
                        'roles', pfw.roles
                    )
                ) AS roles_by_films
                FROM content.person p
                JOIN (
                    SELECT
                        person_id,
                        film_work_id,
                        array_agg(role ORDER BY role) AS roles
                    FROM content.person_film_work
                    GROUP BY person_id, film_work_id
                ) pfw
                    ON pfw.person_id = p.id
                WHERE p.modified > %s
                GROUP BY
                    p.id,
                    p.full_name,
                    p.modified
                ORDER BY p.modified
                LIMIT 100;
                """,
                (last_updated,),
            )

            while results := cursor.fetchmany(size=100):
                info(f"extracting persons: {len(results)} items")
                next.send(
                    PersonFilmwork(
                        id=r.id,
                        full_name=r.full_name,
                        roles_by_films=r.roles_by_films,
                        modified=r.modified,
                    )
                    for r in results
                )
