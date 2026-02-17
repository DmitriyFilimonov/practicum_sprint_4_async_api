from datetime import datetime
from logging import info
from typing import Generator

from process.entities.models import (
    PersonFilmworkESDoc,
    PersonFilmworkESDocRaw,
)
from process.es_client import create_persons_scheme, send_bulk
from state.state import State
from utils import coroutine


@coroutine
def load_persons(
    state_key: str,
    state: State,
) -> Generator[None, list[PersonFilmworkESDocRaw], None]:
    while persons := (yield):
        if state.get_state(state_key) == datetime.min:
            create_persons_scheme()

        last_modified = persons[-1].modified

        send_bulk(
            index="persons",
            bulk=[
                PersonFilmworkESDoc(id=p.id, name=p.name, films=p.films)
                for p in persons
            ],
        )

        info(
            f'''info: {state_key} актуализированы до {str(last_modified)}.
            Обновлений: {len(persons)}'''
        )

        state.set_state(key=state_key, value=last_modified)
