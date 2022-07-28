import abc
import json
from typing import Any, Optional


class BaseStorage:
    @abc.abstractmethod
    def save_state(self, key: str, value: str) -> None:
        pass

    @abc.abstractmethod
    def retrieve_state(self, key) -> dict:
        pass


class JsonFileStorage(BaseStorage):
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path

    def create_json_storage(self):
        starting_dates = {
            "last_film_work_check": "1000-01-01",
            "last_genre_check": "1000-01-01",
            "last_person_check": "1000-01-01"
        }
        with open(self.file_path, "w") as file:
            json.dump(starting_dates, file)

    def save_state(self, key: str, value: str) -> None:
        """Save state in permanent JSON storage"""
        with open(self.file_path, "r+") as file:
            # получаем полный словарь со всеми состояниями и добавляем/перезаписываем новое значение
            states_dict = json.load(file)
            states_dict[key] = value
            # перезаписываем данные в JSON файле
            file.seek(0)
            json.dump(states_dict, file)
            file.truncate()

    def retrieve_state(self, key) -> dict:
        """Download state for specific key from permanent JSON storage.
        Returns empy dict if there are no state for this key"""
        with open(self.file_path, "r") as file:
            states_dict = json.load(file)
        state = states_dict.get(key)
        return state


class State:
    def __init__(self, storage: BaseStorage):
        self.storage = storage
        self.local_storage = {}

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа"""
        self.local_storage[key] = value
        self.storage.save_state(key, value)

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу"""
        state = self.storage.retrieve_state(key)
        return state if state else None
