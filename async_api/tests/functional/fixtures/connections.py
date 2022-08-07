import aioredis
import pytest
from elasticsearch import AsyncElasticsearch
from settings import test_settings

ES_URL = f'{test_settings.es_host}:{test_settings.es_port}'


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
