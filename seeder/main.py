import backoff
from logging import info
from datetime import datetime, timedelta
import random
import uuid
import psycopg

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def get_dsl():
    return {
        "dbname": "theatre",
        "user": "postgres",
        "password": "secret",
        "host": "db",
        "port": 5432,
    }


BASE_TITLES = [
    "Star",
    "Galaxy",
    "Empire",
    "Return",
    "Rise",
    "Shadow",
    "Legacy",
    "Chronicles",
    "War",
    "Beyond",
]

BASE_GENRES = [
    "drama",
    "comedy",
    "thriller",
    "horror",
    "history",
    "biography",
    "sci-fi",
    "fantasy",
]


def random_datetime():
    return datetime.utcnow() - timedelta(days=random.randint(0, 5000))


def generate_films(start: int, count: int):
    for i in range(start, start + count):
        title = f"{random.choice(BASE_TITLES)} {i}"

        yield (
            str(uuid.uuid4()),
            title,
            f"Description for {title}",
            None,
            round(random.uniform(4.0, 9.5), 1),
            "movie",
            random_datetime(),
            random_datetime(),
        )


def generate_genres(start: int, count: int):
    for i in range(start, start + count):
        name = f"{random.choice(BASE_GENRES)} {i}"

        yield (
            str(uuid.uuid4()),
            name,
            "Description",
            random_datetime(),
            random_datetime(),
        )


BATCH_SIZE = 10000
FILMS_COUNT = 250000

GENRES_CONUT = 110


def add_films_batch(connection: psycopg.Connection, cursor: psycopg.Cursor, inserted):
    films = generate_films(start=inserted, count=BATCH_SIZE)
    _films = [film for film in films]

    with connection.transaction():
        cursor.executemany(
            """
            INSERT INTO content.film_work
            (id, title, description, creation_date, rating, type, created, modified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            _films,
        )

    info(f"Добавлено фильмов: {inserted + BATCH_SIZE}")

    return _films


def add_genres_batch(connection: psycopg.Connection, cursor: psycopg.Cursor, inserted):
    genres = generate_genres(start=inserted, count=BATCH_SIZE)
    _genres = [genre for genre in genres]

    with connection.transaction():
        cursor.executemany(
            """
            INSERT INTO content.genre
            (id, name, description, created, modified)
            VALUES (%s, %s, %s, %s, %s)
            """,
            _genres,
        )

    info(f"Добавлено жанров: {inserted + BATCH_SIZE}")

    return _genres


def generate_genre_film_work_links(
    added_films_ids: list[str], added_genres_ids: list[str]
):
    for film_id in added_films_ids:
        genres = random.sample(
            added_genres_ids,
            k=random.randint(1, 3),
        )
        for genre_id in genres:
            yield (
                str(uuid.uuid4()),
                genre_id,
                film_id,
                random_datetime(),
            )


def create_genre_film_work_links(
    connection: psycopg.Connection,
    cursor: psycopg.Cursor,
    added_films_ids: list[str],
    added_genres_ids: list[str],
):
    links = generate_genre_film_work_links(
        added_films_ids=added_films_ids, added_genres_ids=added_genres_ids
    )

    with connection.transaction():
        cursor.executemany(
            """
            INSERT INTO content.genre_film_work
            (id, genre_id, film_work_id, created)
            VALUES (%s, %s, %s, %s)
            """,
            links,
        )


CON_ERRORS = (psycopg.OperationalError,)


@backoff.on_exception(
    backoff.expo,
    CON_ERRORS,
    max_time=60,
    jitter=backoff.full_jitter,
)
def get_connection():
    return psycopg.connect(**get_dsl())


if __name__ == "__main__":
    with (
        get_connection() as connection,
        psycopg.Cursor(connection=connection) as cursor,
    ):
        added_genres = add_genres_batch(
            connection=connection, cursor=cursor, inserted=0
        )

        added_genres_ids = [added_genre[0] for added_genre in added_genres]

        inserted = 0

        while inserted < FILMS_COUNT:
            added_films = add_films_batch(
                connection=connection, cursor=cursor, inserted=inserted
            )

            inserted += BATCH_SIZE

            added_films_ids = [added_film[0] for added_film in added_films]

            create_genre_film_work_links(
                connection=connection,
                cursor=cursor,
                added_films_ids=added_films_ids,
                added_genres_ids=added_genres_ids,
            )
