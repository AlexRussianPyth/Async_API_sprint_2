from functools import lru_cache

import json
from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.models import Person
from core.utils import generate_cache_key
from core.config import api_settings, cache_settings


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, person_id: str) -> Person | None:
        """Возвращает Человека по id"""
        # Пытаемся получить данные из кеша, потому что он работает быстрее
        person = await self._get_person_from_cache(person_id)

        if not person:
            # Если человека нет в кеше, то ищем его в Elasticsearch
            person = await self._get_person_from_elastic(person_id)

            if not person:
                # Если он отсутствует в Elasticsearch, значит, человека вообще нет в базе
                return None

            # А если человек в Elastic есть, то сохраняем в кеш
            await self._put_person_to_cache(person)

        return person

    async def search_persons(self, query: str | None, page: int) -> list[Person] | None:
        """Возвращает массив Людей из базы Elastic либо кэша Редиса"""
        persons = await self._get_persons_chunk_from_cache(page=page, query=query)
        if not persons:
            # Если массива с Людьми нет в кэше, то ищем его в Эластике
            persons = await self._get_persons_chunk_from_elastic(page, query)
            if not persons:
                return None
            await self._put_persons_chunk_to_cache(persons, query, page)

        return persons

    async def films_by_person(self, person_name: str) -> list | None:
        """Возвращает данные о фильмах, в которых участвовал Человек с данным именем"""
        films_with_person = await self.elastic.search(
            index='movies',
            body={
                "query": {
                    "multi_match": {
                        "query": person_name,
                        "fields": ["director", "actors_names", "writers_names"]
                    }
                }
            }
        )
        films_ids = set()
        for film in films_with_person['hits']['hits']:
            films_ids.add(film['_id'])

        return list(films_ids)

    async def _get_persons_chunk_from_elastic(self, page: int, query: str = None) -> list[Person] | None:
        """Достает несколько записей (или все) о Людях из Эластика, используя пагинацию"""
        if query:
            body = {
                "query": {
                    "fuzzy": {
                        "full_name": {
                            "value": query, "fuzziness": "AUTO"
                        }
                    }
                }
            }
        else:
            body = None
        try:
            query_result = await self.elastic.search(
                index='persons',
                body=body,
                from_=(page - 1) * int(api_settings.page_size),
                size=api_settings.page_size,
            )
        except NotFoundError:
            return None

        persons = []

        for doc in query_result['hits']['hits']:
            person_name = doc['_source']['full_name']
            films_ids = await self.films_by_person(person_name)

            person_data = doc['_source']
            person_data['films_ids'] = films_ids

            persons.append(Person(**person_data))

        return persons

    async def _get_persons_chunk_from_cache(self, page: int, query: str | None):
        """Получает массив объектов Человек из кэша Редиса"""
        # Определяем ключ кеширования
        cache_key = await generate_cache_key(
            index="persons",
            query=query,
            page=page
        )

        data = await self.redis.get(cache_key)

        if not data:
            return None

        return [Person.parse_raw(person) for person in json.loads(data)]

    async def _put_persons_chunk_to_cache(self, persons_chunk, search_query: str | None, page: int) -> None:
        """Сохранит лист Людей в кэше Редиса"""
        # Получаем ключ для кеширования
        cache_key = await generate_cache_key(
            index="persons",
            query=search_query,
            page=page
        )

        data = [chunk.json() for chunk in persons_chunk]

        await self.redis.set(
            key=cache_key,
            value=json.dumps(data),
            expire=cache_settings.person_cache_expire_sec
        )

    async def _get_person_from_elastic(self, person_id: str) -> Person | None:
        try:
            doc = await self.elastic.get('persons', person_id)
        except NotFoundError:
            return None

        if doc:
            person_name = doc['_source']['full_name']
            # Найдем в Эластике список фильмов, в которых участвовал данный человек
            films_ids = await self.films_by_person(person_name)

            # Добавим в словарь с данными о человеке данные о фильмах и ролях
            person_data = doc['_source']
            person_data['films_ids'] = films_ids

        return Person(**person_data)

    async def _get_person_from_cache(self, person_id: str) -> Person | None:
        # Пытаемся получить данные о человеке из кеша, используя команду get
        data = await self.redis.get(person_id)
        if not data:
            return None

        # pydantic предоставляет удобное API для создания объекта моделей из json
        person = Person.parse_raw(data)
        return person

    async def _put_person_to_cache(self, person: Person):
        # Сохраняем данные о человеке, используя команду set
        await self.redis.set(person.id, person.json(), expire=cache_settings.person_cache_expire_sec)


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
