from logging import info
from datetime import datetime
from typing import Generator

from process.es_client import create_scheme, send_bulk
from state.state import State
from process.entities.models import (
    GenreFilmworkESDoc,
    GenreFilmworkESDocRaw,
)

from utils import coroutine


@coroutine
def load_genres(
    state_key: str,
    state: State,
) -> Generator[None, list[GenreFilmworkESDocRaw], None]:
    while genres := (yield):
        if state.get_state(state_key) == datetime.min:
            create_scheme()

        last_modified = genres[-1].modified

        send_bulk(
            index="genres",
            bulk=[
                GenreFilmworkESDoc(
                    id=g.id,
                    name=g.name,
                    description=g.description,
                )
                for g in genres
            ],
        )

        info(
            f"info: {state_key} актуализированы до {str(last_modified)}. Обновлений: {len(genres)}"
        )

        state.set_state(key=state_key, value=last_modified)
