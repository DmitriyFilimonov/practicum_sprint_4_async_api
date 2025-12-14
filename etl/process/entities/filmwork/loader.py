from logging import info
from datetime import datetime
from typing import Generator

from process.es_client import create_scheme, send_bulk
from state.state import State
from process.entities.models import FilmWorkESDoc, FilmWorkESDocRaw

from utils import coroutine


@coroutine
def load_movies(
    state_key: str,
    state: State,
) -> Generator[None, list[FilmWorkESDocRaw], None]:
    while filmworks := (yield):
        if state.get_state(state_key) == datetime.min:
            create_scheme()

        last_modified = filmworks[-1].modified

        send_bulk(
            bulk=[
                FilmWorkESDoc(
                    actors=f.actors,
                    actors_names=f.actors_names,
                    description=f.description,
                    directors=f.directors,
                    directors_names=f.directors_names,
                    genres=f.genres,
                    id=f.id,
                    imdb_rating=f.imdb_rating,
                    title=f.title,
                    writers=f.writers,
                    writers_names=f.writers_names,
                )
                for f in filmworks
            ]
        )

        info(
            f"info: {state_key} актуализированы до {str(last_modified)}. Обновлений: {len(filmworks)}"
        )

        state.set_state(key=state_key, value=last_modified)
