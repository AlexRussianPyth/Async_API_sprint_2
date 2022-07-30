from functools import lru_cache

import json
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.bases.cache import BaseCacheService
from db.elastic import get_elastic
from db.redis import get_redis
from models.models import Genre
from core.utils import generate_cache_key
from core.config import api_settings, cache_settings


class GenreService:
    """Класс, который позволяет вернуть данные о жанрах напрямую из Эластика либо опосредованно из Redis"""

    def __init__(self, cache_service: BaseCacheService, elastic: AsyncElasticsearch):
        self.cache_service = cache_service
        self.elastic = elastic

    async def get_genres(self, page: int, query: str | None) -> list[Genre] | None:
        """Возвращает жанры из базы Эластик либо из кэша Рэдиса"""
        genres = await self._get_genres_chunk_from_cache(page=page, query=query)
        if not genres:
            # Если массива с Жанрами нет в кэше, то ищем его в Эластике
            genres = await self._get_genres_chunk_from_elastic(page, query)
            if not genres:
                return None
            await self._put_genres_chunk_to_cache(genres, query, page)

        return genres

    async def get_by_id(self, genre_id: str) -> Genre | None:
        """Возвращает объект жанра. Он опционален, так как жанр может отсутствовать в базе"""
        genre = await self._get_genre_from_cache(genre_id)
        if not genre:
            # Если фильма нет в кеше, то ищем его в Elasticsearch
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                # Если он отсутствует в Elasticsearch, значит, жанра вообще нет в базе
                return None
            # Сохраняем фильм  в кеш
            await self._put_genre_to_cache(genre)

        return genre

    async def _get_genres_chunk_from_elastic(self, page: int, query: str = None) -> list[Genre] | None:
        """Достает несколько записей (или все) о жанрах из Эластика, используя пагинацию"""
        if query:
            body = {
                'query': {
                    'match': {"name": query}
                }
            }
        else:
            body = None

        try:
            result = await self.elastic.search(
                index='genres',
                body=body,
                from_=(page - 1) * int(api_settings.page_size),
                size=api_settings.page_size,
            )
        except NotFoundError:
            return None

        all_genres = []
        for doc in result['hits']['hits']:
            all_genres.append(Genre(**doc['_source']))

        await self._put_genres_chunk_to_cache(all_genres, query, page)

        return all_genres

    async def _get_genres_chunk_from_cache(self, page: int, query: str | None):
        """Получает массив объектов Жанр из кэша Редиса"""
        # Определяем ключ кеширования
        cache_key = await generate_cache_key(
            index="genres",
            query=query,
            page=page
        )

        data = await self.cache_service.get(cache_key)

        if not data:
            return None

        return [Genre.parse_raw(genre) for genre in json.loads(data)]

    async def _put_genres_chunk_to_cache(self, genres_chunk: list[Genre], search_query: str | None, page: int):
        """Сохранит лист жанров в кэше Редиса"""
        # Получаем ключ для кеширования
        cache_key = await generate_cache_key(
            index="genres",
            query=search_query,
            page=page
        )

        data = [chunk.json() for chunk in genres_chunk]

        await self.cache_service.set(
            key=cache_key,
            value=json.dumps(data),
            expire=cache_settings.genre_cache_expire_sec
        )

    async def _get_genre_from_elastic(self, genre_id: str) -> Genre | None:
        """Получает объект Жанра по id из Эластика"""
        try:
            doc = await self.elastic.get('genres', genre_id)
        except NotFoundError:
            return None
        return Genre(**doc['_source'])

    async def _get_genre_from_cache(self, genre_id: str) -> Genre | None:
        """Получает объект Жанра по id из Кэша в Рэдис"""
        data = await self.cache_service.get(genre_id)
        if not data:
            return None
        # pydantic предоставляет удобное API для создания объекта моделей из json
        genre = Genre.parse_raw(data)
        return genre

    async def _put_genre_to_cache(self, genre: Genre):
        """Сохраняет объект Жанра в Кэш Рэдиса"""
        await self.cache_service.set(genre.id, genre.json(), expire=cache_settings.genre_cache_expire_sec)


@lru_cache()
def get_genre_service(
        cache_service: BaseCacheService = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    """Функция возвращает синглтон объект GenreService с внедренными зависимостями"""
    return GenreService(cache_service, elastic)
