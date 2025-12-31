import backoff
from logging import info
from datetime import datetime, timedelta
import random
import uuid
import psycopg


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


BATCH_SIZE = 100
FILMS_COUNT = 200000


def add_batch(cursor, inserted):
    films = generate_films(start=inserted, count=BATCH_SIZE)
    cursor.executemany(
        """
        INSERT INTO content.film_work
        (id, title, description, creation_date, rating, type, created, modified)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        films,
    )
    info(f"Добавлено фильмов: {inserted}")


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
        inserted = 0

        while inserted < FILMS_COUNT:
            add_batch(cursor=cursor, inserted=inserted)

            inserted += BATCH_SIZE
