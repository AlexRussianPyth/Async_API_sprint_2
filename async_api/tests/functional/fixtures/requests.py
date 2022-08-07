import asyncio

import aiohttp
import pytest
from settings import test_settings
from utils.models import HTTPResponse

FASTAPI_URL = f'{test_settings.fastapi_host}:{test_settings.fastapi_port}'


@pytest.fixture
def event_loop():
    yield asyncio.get_event_loop()


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