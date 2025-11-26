import psycopg
from utils import backoff
from process.entities.models import FilmWork
from process.entities.filmwork.etl import movies_etl
from state.state import JsonFileStorage, State
from psycopg.rows import class_row
from settings import settings

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


@backoff(border_sleep_time=60)
def start_etl():

    storage = JsonFileStorage()
    state = State(storage)

    movies_etl(state=state)


if __name__ == "__main__":
    start_etl()
