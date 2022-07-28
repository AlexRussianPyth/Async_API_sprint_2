from functools import lru_cache

import json
from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from core.utils import generate_cache_key
from core.config import cache_settings
from db.elastic import get_elastic
from db.redis import get_redis
from models.models import Film


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    # get_by_id возвращает объект фильма. Он опционален, так как фильм может отсутствовать в базе
    async def get_by_id(self, film_id: str) -> Film | None:
        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        film = await self._get_film_from_cache(film_id)
        if not film:
            # Если фильма нет в кеше, то ищем его в Elasticsearch
            film = await self._get_film_from_elastic(film_id)
            if not film:
                # Если он отсутствует в Elasticsearch, значит, фильма вообще нет в базе
                return None
            # Сохраняем фильм  в кеш
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
        """Возвращает набор фильмов из базы Elastic"""
        """Возвращает жанры из базы Эластик либо из кэша Рэдиса"""
        films = await self._get_films_chunk_from_cache(
            page=page,
            query=query,
            page_size=page_size,
            sort=sort,
            filter_genre=filter_genre
        )
        if not films:
            # Если массива с Фильмами нет в кэше, то ищем его в Эластике
            films = await self._get_films_chunk_from_elastic(
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

    async def _get_films_chunk_from_elastic(
            self,
            query: str | None,
            page: int,
            page_size: int,
            sort: str,
            filter_genre: str,
    ) -> list[Film] | None:
        """Достает несколько записей (или все) о фильмах из Эластика, используя пагинацию"""
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
            result = await self.elastic.search(
                index='movies',
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
        """Получает массив объектов Фильм из кэша Редиса"""
        # Определяем ключ кеширования
        cache_key = await generate_cache_key(
            index="films",
            **kwargs
        )

        data = await self.redis.get(cache_key)
        if not data:
            return None

        return [Film.parse_raw(film) for film in json.loads(data)]

    async def _put_films_chunk_to_cache(self, films_chunk, **kwargs) -> None:
        """Сохранит лист Фильмов в кэше Редиса"""
        # Получаем ключ для кеширования
        cache_key = await generate_cache_key(
            index="films",
            **kwargs
        )

        data = [chunk.json() for chunk in films_chunk]

        await self.redis.set(
            key=cache_key,
            value=json.dumps(data),
            expire=cache_settings.film_cache_expire_sec
        )

    async def _get_film_from_elastic(self, film_id: str) -> Film | None:
        try:
            doc = await self.elastic.get('movies', film_id)
        except NotFoundError:
            return None

        return Film(**doc['_source'])

    async def _get_film_from_cache(self, film_id: str) -> Film | None:
        data = await self.redis.get(film_id)
        if not data:
            return None

        # pydantic предоставляет удобное API для создания объекта моделей из json
        film = Film.parse_raw(data)
        return film

    async def _put_film_to_cache(self, film: Film) -> None:
        await self.redis.set(film.id, film.json(), expire=cache_settings.film_cache_expire_sec)


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
