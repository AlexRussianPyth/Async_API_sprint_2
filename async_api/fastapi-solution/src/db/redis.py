import abc
from abc import ABC

from aioredis import Redis

redis: Redis | None = None


# Функция понадобится при внедрении зависимостей
# async def get_redis() -> Redis:
#     return redis

# var2
async def get_redis() -> Redis:
    return RedisCacheService(redis)

class BaseCacheService(ABC):
    @abc.abstractmethod
    def get(self, key: str):
        raise NotImplemented

    @abc.abstractmethod
    def set(self, key: str, value: str, expire: int):
        raise NotImplemented

class RedisCacheService(BaseCacheService):
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> str:
        return await self.redis.get(key)

    async def set(self, key: str, value: str, expire: int) -> None:
        return await self.redis.set(
            key,
            value,
            expire=expire
        )