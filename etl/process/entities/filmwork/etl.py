from time import sleep

from process.entities.person.extractor import extract_movies_by_person_modified
from process.entities.person.constants import PERSONS_STATE_KEY
from process.entities.genre.constants import GENRES_STATE_KEY
from process.entities.genre.extractor import extract_movies_by_genre_modified
from process.entities.filmwork.constants import MOVIES_STATE_KEY
from state.state import State
from process.entities.filmwork.extractor import extract_movies_by_modified
from process.entities.filmwork.transformer import (
    filmwork_modified_extractor,
    genre_modified_extractor,
    person_modified_extractor,
    transform_movies,
)
from process.entities.filmwork.loader import load_movies
from process.entities.filmwork.constants import MOVIES_STATE_KEY


def movies_etl(state: State):
    loader_by_modified = load_movies(state_key=MOVIES_STATE_KEY, state=state)
    transformer_by_modified = transform_movies(
        next=loader_by_modified, last_modified_getter=filmwork_modified_extractor
    )
    extractor_by_modified = extract_movies_by_modified(next=transformer_by_modified)

    loader_by_genre_modified = load_movies(state_key=GENRES_STATE_KEY, state=state)
    transformer_by_genre_modified = transform_movies(
        next=loader_by_genre_modified, last_modified_getter=genre_modified_extractor
    )
    extractor_by_genre_modified = extract_movies_by_genre_modified(
        next=transformer_by_genre_modified
    )

    loader_by_persons_modified = load_movies(state_key=PERSONS_STATE_KEY, state=state)
    transformer_by_person_modified = transform_movies(
        next=loader_by_persons_modified, last_modified_getter=person_modified_extractor
    )
    extractor_by_persons_modified = extract_movies_by_person_modified(
        next=transformer_by_person_modified
    )

    while True:
        extractor_by_modified.send(state.get_state(MOVIES_STATE_KEY))

        extractor_by_genre_modified.send(state.get_state(GENRES_STATE_KEY))

        extractor_by_persons_modified.send(state.get_state(PERSONS_STATE_KEY))

        sleep(15)
