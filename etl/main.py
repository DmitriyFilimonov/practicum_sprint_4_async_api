from threading import Thread
from time import sleep


from process.entities.genre_filmwork.etl import create_genre_film_work_etl
from utils import backoff
from process.entities.filmwork.etl import create_movies_etl
from state.state import RemoteStorage, State

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


@backoff(border_sleep_time=60)
def start_etl():

    state = State(RemoteStorage())

    movies_etl_step = create_movies_etl(state)
    genre_etl_step = create_genre_film_work_etl(state)

    while True:
        movies_etl_step()
        genre_etl_step()

        sleep(15)


if __name__ == "__main__":
    start_etl()
