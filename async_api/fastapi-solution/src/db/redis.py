from aioredis import Redis
from functools import lru_cache

from db.bases.cache import BaseCacheService

redis: Redis | None = None


@lru_cache()
def get_redis() -> BaseCacheService:
    return RedisCacheService(redis)


class RedisCacheService(BaseCacheService):
    def __init__(self, redis_conn: Redis):
        self.redis = redis_conn

    async def get(self, key: str) -> str:
        return await self.redis.get(key)

    async def set(self, key: str, value: str, expire: int) -> None:
        return await self.redis.set(
            key,
            value,
            expire=expire
        )
