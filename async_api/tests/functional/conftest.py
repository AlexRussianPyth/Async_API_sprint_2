import aiohttp
import pytest

import asyncio
from dataclasses import dataclass
import aioredis
from multidict import CIMultiDictProxy
from elasticsearch import AsyncElasticsearch

from .settings import test_settings

FASTAPI_URL = 'http://' + test_settings.fastapi_host + ':' + test_settings.fastapi_port


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
    client = AsyncElasticsearch(hosts='127.0.0.1:9200')
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
    async def inner(method: str, params: dict | None = None) -> HTTPResponse:
        params = params or {}
        url = FASTAPI_URL + '/api/v1' + method  # в боевых системах старайтесь так не делать!
        async with session.get(url, params=params) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )

    return inner

@pytest.fixture(scope='session')
async def genres_index(es_client):
    """Создание и заполнение индекса в Elastic"""

    index_name = 'persons'
    await es_client.indices.create(index=index_name, body=es_persons_index_schema, ignore=400)
    persons = [{"_index": index_name, "_id": obj.get("id"), **obj} for obj in es_persons]
    await async_bulk(client=es_client, actions=persons)
    yield
    # TODO после отладки расскомментировать удаление индекса
    # await es_client.indices.delete(index=index_name)