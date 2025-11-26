import abc
from datetime import datetime
import json
from typing import Any, Dict


class BaseStorage(abc.ABC):
    @abc.abstractmethod
    def save_state(self, state: Dict[str, Any]) -> None: ...

    @abc.abstractmethod
    def retrieve_state(self) -> Dict[str, Any]: ...


class JsonFileStorage(BaseStorage):
    def __init__(self) -> None:
        self.file_path = "./storage/storage.json"

    def save_state(self, state: Dict[str, Any]) -> None:
        with open(self.file_path, "w") as storage_file:
            json.dump(state, storage_file, indent=2)

    def retrieve_state(self) -> Dict[str, Any]:
        try:
            with open(self.file_path, "r") as storage_file:
                return json.load(storage_file)
        except:
            return {}


class State:
    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage

    def set_state(self, state_key: str, value: datetime) -> None:
        state_dict = self.storage.retrieve_state()
        state_dict[state_key] = str(value)
        self.storage.save_state(state_dict)

    def get_state(self, state_key: str) -> datetime:
        # TODO: реализовать
        state_dict = self.storage.retrieve_state()
        raw = state_dict.get(state_key)

        if raw == None:
            return datetime.min

        return datetime.fromisoformat(raw)
