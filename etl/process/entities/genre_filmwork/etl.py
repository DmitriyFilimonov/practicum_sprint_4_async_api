from utils import backoff
from process.entities.genre_filmwork.loader import load_genres
from process.entities.genre_filmwork.contants import GENRES_FILM_WORK_STATE_KEY
from process.entities.genre_filmwork.transformer import transform_genres
from process.entities.genre_filmwork.extractor import extract_genres_by_modified
from state.state import State


def create_genre_film_work_etl(state: State):
    loader_genres = load_genres(state_key=GENRES_FILM_WORK_STATE_KEY, state=state)

    transformer_genres = transform_genres(next=loader_genres)

    extractor_genres = extract_genres_by_modified(next=transformer_genres)

    @backoff(border_sleep_time=60)
    def step():
        extractor_genres.send(state.get_state(GENRES_FILM_WORK_STATE_KEY))

    return step
