from typing import Optional

from elasticsearch import AsyncElasticsearch

from db.bases.storage import AbstractStorage

# todo удалить после ревакторинга
es: Optional[AsyncElasticsearch] = None


# Функция понадобится при внедрении зависимостей
async def get_elastic() -> AsyncElasticsearch:
    return es


class Elastic(AbstractStorage):
    def __init__(self, storage):
        self.storage = storage

    async def get(self, index_name: str, _id: str):
        return await self.storage.get(index_name, _id)

    async def search(self, index: str, body: dict | None, from_: int | None = None, size: int | None = None,
                     sort: str | None = None):
        return await self.storage.search(index=index, body=body, from_=from_, size=size, sort=sort)
