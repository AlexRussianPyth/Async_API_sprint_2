import aiohttp
import pytest

import asyncio
from dataclasses import dataclass
import aioredis
from multidict import CIMultiDictProxy
from elasticsearch import AsyncElasticsearch

from settings import test_settings

FASTAPI_URL = f"http://{test_settings.fastapi_host}:{test_settings.fastapi_port}"


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
    client = AsyncElasticsearch(hosts=f'{test_settings.es_host}:{test_settings.es_port}')
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
