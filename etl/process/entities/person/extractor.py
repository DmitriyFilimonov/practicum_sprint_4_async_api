import psycopg
from process.entities.models import FilmWork
from psycopg.rows import class_row
from settings import settings
from datetime import datetime
from typing import Generator

from utils import coroutine
from process.entities.models import FilmWork


@coroutine
def extract_movies_by_person_modified(
    next: Generator[None, list[FilmWork], None],
) -> Generator[None, datetime, None]:
    with (
        psycopg.connect(
            **settings.get_dsl(), row_factory=class_row(FilmWork)
        ) as connection,
        psycopg.ServerCursor(connection=connection, name="persons_extractor") as cursor,
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
                            'person_role', pfw_selection.role,
                            'person_id', p_selection.id,
                            'person_name', p_selection.full_name
                        )
                    ) FILTER (WHERE p_selection.id is not null),
                    '[]'
                ) as persons,
                array_agg(DISTINCT g.name) as genres
                FROM content.person p_filter
                JOIN content.person_film_work pfw_filter ON pfw_filter.person_id = p_filter.id
                JOIN content.film_work fw ON fw.id = pfw_filter.film_work_id
                
                LEFT JOIN content.person_film_work pfw_selection ON pfw_selection.film_work_id = fw.id
                LEFT JOIN content.person p_selection ON p_selection.id = pfw_selection.person_id
                
                LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
                LEFT JOIN content.genre g ON g.id = gfw.genre_id


                WHERE p_filter.modified > %s
                GROUP BY fw.id
                ORDER BY MAX(p_filter.modified)
                LIMIT 100;
                """,
                (last_updated,),
            )
            while results := cursor.fetchmany(size=100):
                next.send(results)
