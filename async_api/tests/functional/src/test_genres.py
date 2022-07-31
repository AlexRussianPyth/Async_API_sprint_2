import logging

import logging
import pytest


logger = logging.getLogger('test_logger')

@pytest.mark.asyncio
async def test_genre_index_created(es_client, redis_client, make_get_request):
    result = await es_client.indices.exists(index='genres')
    assert result == True

@pytest.mark.asyncio
async def test_genre_index_created(es_client, redis_client, make_get_request):
    result = await es_client.indices.exists(index='genres')
    assert result == True



