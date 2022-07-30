import abc
from abc import ABC


class BaseCacheService(ABC):
    @abc.abstractmethod
    def get(self, key: str):
        raise NotImplementedError

    @abc.abstractmethod
    def set(self, key: str, value: str, expire: int):
        raise NotImplementedError
