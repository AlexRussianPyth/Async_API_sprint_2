from abc import ABC, abstractmethod
from typing import Optional


class AbstractStorage(ABC):
    @abstractmethod
    def get(self, index_name: str, _id: str):
        pass

    @abstractmethod
    def search(self, index: str, body: dict | None, from_: int | None, size: int | None, sort: str | None):
        pass


storage: Optional[AbstractStorage] = None


async def get_storage() -> AbstractStorage:
    return storage
