import json
from functools import lru_cache

from core.config import api_settings, cache_settings
from core.utils import generate_cache_key
from db.bases.cache import BaseCacheService
from db.bases.storage import AbstractStorage, get_storage
from db.redis import get_redis
from elasticsearch import NotFoundError
from fastapi import Depends
from models.models import Genre


class GenreService:
    """Класс, который позволяет вернуть данные о жанрах"""

    def __init__(self, cache_service: BaseCacheService, storage: AbstractStorage, index_name: str = 'genres'):
        self.cache_service = cache_service
        self.storage = storage
        self.index_name = index_name

    async def get_genres(self, page: int, query: str | None) -> list[Genre] | None:
        """Возвращает жанры из базы бд либо из кэша"""

        genres = await self._get_genres_chunk_from_cache(page=page, query=query)
        if not genres:
            # Если массива с Жанрами нет в кэше, то ищем его в бд
            genres = await self._get_genres_chunk_from_db(page, query)
            if not genres:
                return None
            await self._put_genres_chunk_to_cache(genres, query, page)

        return genres

    async def get_by_id(self, genre_id: str) -> Genre | None:
        """Возвращает объект жанра. Он опционален, так как жанр может отсутствовать в базе"""

        genre = await self._get_genre_from_cache(genre_id)
        if not genre:
            # Если фильма нет в кеше, то ищем его в бд
            genre = await self._get_genre_from_db(genre_id)
            if not genre:
                # Если он отсутствует в бд, значит, жанра вообще нет в базе
                return None
            # Сохраняем жанр в кеш
            await self._put_genre_to_cache(genre)

        return genre

    async def _get_genres_chunk_from_db(self, page: int, query: str = None) -> list[Genre] | None:
        """Достает несколько записей (или все) о жанрах из бд, используя пагинацию"""

        if query:
            body = {
                'query': {
                    'match': {"name": query}
                }
            }
        else:
            body = None

        try:
            result = await self.storage.search(
                index=self.index_name,
                body=body,
                from_=(page - 1) * int(api_settings.page_size),
                size=api_settings.page_size
            )
        except NotFoundError:
            return None

        all_genres = []
        for doc in result['hits']['hits']:
            all_genres.append(Genre(**doc['_source']))

        await self._put_genres_chunk_to_cache(all_genres, query, page)

        return all_genres

    async def _get_genres_chunk_from_cache(self, page: int, query: str | None):
        """Получает массив объектов Жанр из кэша"""

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
        """Сохранит лист жанров в кэше"""

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

    async def _get_genre_from_db(self, genre_id: str) -> Genre | None:
        """Получает объект Жанра по id из бд"""

        try:
            doc = await self.storage.get(self.index_name, genre_id)
        except NotFoundError:
            return None
        return Genre(**doc['_source'])

    async def _get_genre_from_cache(self, genre_id: str) -> Genre | None:
        """Получает объект Жанра по id из Кэша"""

        data = await self.cache_service.get(genre_id)
        if not data:
            return None
        genre = Genre.parse_raw(data)
        return genre

    async def _put_genre_to_cache(self, genre: Genre):
        """Сохраняет объект Жанра в Кэш"""

        await self.cache_service.set(genre.id, genre.json(), expire=cache_settings.genre_cache_expire_sec)


@lru_cache()
def get_genre_service(
        cache_service: BaseCacheService = Depends(get_redis),
        storage: AbstractStorage = Depends(get_storage),
) -> GenreService:
    """Функция возвращает синглтон объект GenreService с внедренными зависимостями"""
    return GenreService(cache_service, storage)
