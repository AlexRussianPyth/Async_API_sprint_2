import asyncio
import json
from dataclasses import dataclass

import aiohttp
import aioredis
import pytest
from elasticsearch import AsyncElasticsearch
from elasticsearch._async.helpers import async_bulk
from multidict import CIMultiDictProxy

from settings import test_settings
from testdata.es_index import es_films_index_schema, es_persons_index_schema
from testdata.persons_data import es_persons

FASTAPI_URL = f'{test_settings.fastapi_host}:{test_settings.fastapi_port}'
ES_URL = f'{test_settings.es_host}:{test_settings.es_port}'


@dataclass
class HTTPResponse:
    body: dict
    headers: CIMultiDictProxy[str]
    status: int


@pytest.fixture
def event_loop():
    yield asyncio.get_event_loop()


@pytest.fixture(scope='session')
async def es_client():
    """Управляет соединением с сервисом Elastic"""
    client = AsyncElasticsearch(hosts=ES_URL)
    yield client
    await client.close()


@pytest.fixture(scope='session')
async def redis_client():
    """Управляет соединением с Redis"""
    redis = await aioredis.create_redis_pool(address=(test_settings.redis_host, test_settings.redis_port))
    yield redis
    redis.close()
    await redis.wait_closed()


@pytest.fixture(scope='session')
async def session():
    """Возвращает интерфейс для проведения HTTP запросов"""
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest.fixture
def make_get_request(session):
    """Фикстура для отправки GET запросов.
    Input:
        endpoint - конечный метод нашего RestAPI
        params: параметры для запроса
    Output:
        Объект HTTPResponse
    """

    async def inner(endpoint: str, params: dict | None = None) -> HTTPResponse:
        params = params or {}
        url = f'{FASTAPI_URL}{endpoint}'
        async with session.get(url, params=params) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )

    return inner


@pytest.fixture(scope='session')
async def persons_index(es_client):
    """Создание и заполнение индекса в Elastic"""

    index_name = 'persons'
    await es_client.indices.create(index=index_name, body=es_persons_index_schema, ignore=400)
    persons = [{"_index": index_name, "_id": obj.get("id"), **obj} for obj in es_persons]
    await async_bulk(client=es_client, actions=persons)
    await es_client.indices.refresh(index=[index_name, ])

    yield

    await es_client.indices.delete(index=index_name)


@pytest.fixture(scope='session')
async def movies_index(es_client):
    """Создание и заполнение индекса в Elastic"""

    index_name = 'movies'
    await es_client.indices.create(index=index_name, body=es_films_index_schema, ignore=400)
    with open('./testdata/movies.json') as file:
        es_films = json.load(file)
    films = []
    for es_film in es_films:
        film = {
            "_index": index_name,
            "_id": es_film.get("id"),
            "id": es_film.get("id"),
            "title": es_film.get("title"),
            "description": es_film.get("description"),
            "imdb_rating": es_film.get("imdb_rating"),
            "genre": es_film.get("genre"),
            "actors": es_film.get("actors"),
            "writers": es_film.get("writers"),
            "actors_names": es_film.get("actors_names"),
            "writers_names": es_film.get("writers_names"),
            "director": es_film.get("director"),

        }
        films.append(film)
    await async_bulk(client=es_client, actions=films)
    await es_client.indices.refresh(index=[index_name, ])

    yield

    await es_client.indices.delete(index=index_name)


@pytest.fixture(scope='session')
def get_films():
    def inner(schema):
        with open('./testdata/movies.json') as file:
            es_films = json.load(file)
        return [schema(**es_film, uuid=es_film['id'], directors=es_film['director']) for es_film in es_films]

    return inner
