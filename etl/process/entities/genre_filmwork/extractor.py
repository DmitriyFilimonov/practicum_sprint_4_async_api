import psycopg
from process.entities.models import (
    GenreFilmwork,
)
from psycopg.rows import class_row
from settings import settings
from datetime import datetime
from typing import Generator

from utils import coroutine
from process.entities.models import FilmWork


@coroutine
def extract_movies_by_modified(
    next: Generator[None, list[GenreFilmwork], None],
) -> Generator[None, datetime, None]:

    with (
        psycopg.connect(
            **settings.get_dsl(), row_factory=class_row(GenreFilmwork)
        ) as connection,
        psycopg.ServerCursor(
            connection=connection, name="genre_filmwork__extractor"
        ) as cursor,
    ):
        while last_updated := (yield):
            cursor.execute(
                """
                SELECT DISTINCT
                    g.id,
                    g.name,
                    g.modified,
                    g.description
                FROM content.genre g
                JOIN (
                    SELECT 
                    gf.genre_id
                    FROM content.genre_film_work gf
                ) gfi
                ON
                    gfi.genre_id = g.id
                WHERE g.modified > %s
                ;
                """,
                (last_updated,),
            )

            while results := cursor.fetchmany(size=100):
                next.send(
                    GenreFilmwork(
                        id=r.id,
                        name=r.name,
                        description=r.description,
                        modified=r.modified,
                    )
                    for r in results
                )
