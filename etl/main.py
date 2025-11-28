from utils import backoff
from process.entities.filmwork.etl import movies_etl
from state.state import RemoteStorage, State

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


@backoff(border_sleep_time=60)
def start_etl():

    state = State(RemoteStorage())

    movies_etl(state=state)


if __name__ == "__main__":
    start_etl()
