import json
from functools import lru_cache

from core.config import cache_settings
from core.utils import generate_cache_key
from db.bases.cache import BaseCacheService
from db.bases.storage import AbstractStorage, get_storage
from db.redis import get_redis
from elasticsearch import NotFoundError
from fastapi import Depends
from models.models import Film


class FilmService:
    def __init__(self, cache_service: BaseCacheService, storage: AbstractStorage, index_name: str = 'movies'):
        self.cache_service = cache_service
        self.storage = storage
        self.index_name = index_name

    async def get_by_id(self, film_id: str) -> Film | None:
        """Возвращает объект фильма"""

        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        film = await self._get_film_from_cache(film_id)
        if not film:
            # Если фильма нет в кеше, то ищем его в бд
            film = await self._get_film_from_db(film_id)
            if not film:
                # Если он отсутствует в бд, значит, фильма вообще нет в базе
                return None
            # Сохраняем фильм в кеш
            await self._put_film_to_cache(film)

        return film

    async def get_films(
            self,
            page: int,
            page_size: int,
            query: str | None = None,
            filter_genre: str | None = None,
            sort: str | None = None
    ) -> list[Film] | None:
        """Возвращает набор фильмов по определенным параметрам"""

        films = await self._get_films_chunk_from_cache(
            page=page,
            query=query,
            page_size=page_size,
            sort=sort,
            filter_genre=filter_genre
        )
        if not films:
            # Если массива с Фильмами нет в кэше, то ищем его в бд
            films = await self._get_films_chunk_from_db(
                page=page,
                query=query,
                page_size=page_size,
                sort=sort,
                filter_genre=filter_genre
            )
            if not films:
                return None
            await self._put_films_chunk_to_cache(
                films,
                page=page,
                query=query,
                page_size=page_size,
                sort=sort,
                filter_genre=filter_genre
            )

        return films

    async def _get_films_chunk_from_db(
            self,
            query: str | None,
            page: int,
            page_size: int,
            sort: str,
            filter_genre: str,
    ) -> list[Film] | None:
        """Достает несколько записей (или все) о фильмах из бд, используя пагинацию"""

        if query:
            body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title", "description"]
                    }
                }
            }
        else:
            body = {"query": {}}

        if filter_genre:
            body['query']['match'] = {
                        "genre": {"query": filter_genre}
                    }

        if filter_genre is None and query is None:
            body = None

        try:
            result = await self.storage.search(
                index=self.index_name,
                body=body,
                from_=(page - 1) * int(page_size),
                size=page_size,
                sort=sort
            )
        except NotFoundError:
            return None

        all_films = []

        for doc in result['hits']['hits']:
            film_model = Film(**doc['_source'])
            all_films.append(film_model)

        return all_films

    async def _get_films_chunk_from_cache(self, **kwargs) -> list[Film] | None:
        """Получает массив объектов Фильм из сервиса кэширования"""

        # Определяем ключ кеширования
        cache_key = await generate_cache_key(
            index="films",
            **kwargs
        )
        # получаем объект из сервиса кэширование
        data = await self.cache_service.get(cache_key)
        if not data:
            return None

        return [Film.parse_raw(film) for film in json.loads(data)]

    async def _put_films_chunk_to_cache(self, films_chunk, **kwargs) -> None:
        """Сохранит лист Фильмов в сервисе кэширования"""

        # Получаем ключ для кеширования
        cache_key = await generate_cache_key(
            index="films",
            **kwargs
        )

        data = [chunk.json() for chunk in films_chunk]

        await self.cache_service.set(
            key=cache_key,
            value=json.dumps(data),
            expire=cache_settings.film_cache_expire_sec
        )

    async def _get_film_from_db(self, film_id: str) -> Film | None:
        try:
            doc = await self.storage.get(self.index_name, film_id)
        except NotFoundError:
            return None

        return Film(**doc['_source'])

    async def _get_film_from_cache(self, film_id: str) -> Film | None:
        data = await self.cache_service.get(film_id)
        if not data:
            return None

        # pydantic предоставляет удобное API для создания объекта моделей из json
        film = Film.parse_raw(data)
        return film

    async def _put_film_to_cache(self, film: Film) -> None:
        await self.cache_service.set(film.id, film.json(), expire=cache_settings.film_cache_expire_sec)


@lru_cache()
def get_film_service(
        cache_service: BaseCacheService = Depends(get_redis),
        storage: AbstractStorage = Depends(get_storage),
) -> FilmService:
    return FilmService(cache_service, storage)
