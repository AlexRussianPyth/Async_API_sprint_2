import asyncio
import json
from dataclasses import dataclass

import aiohttp
import aioredis
import pytest
from elasticsearch import AsyncElasticsearch
from elasticsearch._async.helpers import async_bulk
from multidict import CIMultiDictProxy

from async_api.tests.functional.settings import test_settings
from async_api.tests.functional.testdata.es_index import es_persons_index_schema, es_films_index_schema
from async_api.tests.functional.testdata.persons_data import es_persons

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
        method - конечный метод нашего RestAPI
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
    yield
    await es_client.indices.delete(index=index_name)
