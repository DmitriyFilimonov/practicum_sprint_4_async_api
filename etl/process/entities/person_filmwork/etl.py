from process.entities.person_filmwork.extractor import extract_persons_by_modified
from process.entities.person_filmwork.transformer import transform_persons
from process.entities.person_filmwork.constants import PERSONS_FILM_WORK_STATE_KEY
from process.entities.person_filmwork.loader import load_persons
from utils import backoff

from state.state import State


def create_person_film_work_etl(state: State):
    loader_genres = load_persons(state_key=PERSONS_FILM_WORK_STATE_KEY, state=state)

    transformer_genres = transform_persons(next=loader_genres)

    extractor_genres = extract_persons_by_modified(next=transformer_genres)

    @backoff(border_sleep_time=60)
    def step():
        extractor_genres.send(state.get_state(PERSONS_FILM_WORK_STATE_KEY))

    return step
