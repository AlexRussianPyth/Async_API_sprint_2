import logging
import pytest

from elasticsearch.exceptions import NotFoundError

from .es_index import es_genres_index_schema
from ..utils.cache import generate_cache_key

logger = logging.getLogger('test_logger')

index_name = 'genres'

@pytest.mark.asyncio
async def test_genre_index_created(es_client, redis_client, make_get_request):
    if not await es_client.indices.exists(index=index_name):
        await es_client.indices.create(index=index_name, ignore=400, body=es_genres_index_schema)
    assert await es_client.indices.exists(index=index_name) == True, \
        f"Индекс с заданным именем {index_name} не был создан"



@pytest.mark.asyncio
async def test_add_genre_doc(es_client, redis_client, make_get_request):
    # 2 Добавляем жанр в индекс
    doc = {
        'id': '45e5cff4-11b0-11ed-861d-0242ac120002',
        'name': 'TestAdventure'
    }
    res = await es_client.index(index='genres', doc_type="_doc", id=1, body=doc)
    # Проверяем, что жанр добавился
    genre = await es_client.get(index='genres', id=1)
    assert genre['found'] == True
    # Проверяем, что мы не находим документы по несуществующим id
    with pytest.raises(NotFoundError):
        genre = await es_client.get(index='genres', id=55)

@pytest.mark.asyncio
async def test_get_by_redis_key(es_client, redis_client, make_get_request):
    # 3 Чистим кэш Рэдиса
    redis_client.flushall()

    # Рэдис
    cache_key = await generate_cache_key('genres', page=2)
    value = b"Some text"
    await redis_client.set(
        key=cache_key,
        value=value,
        expire=1000
    )

    cached_result = await redis_client.get(cache_key)
    assert cached_result == value

@pytest.mark.asyncio
async def test_make_genres_request(es_client, redis_client, make_get_request):
    # Посылаем запрос в сервис
    response = await make_get_request("/genres")
    assert response.status == 200
    assert(len(response.body)) == 1
    #
    # # Удаляем документ по id
    #
    # # Удаляем индекс целиком
    await es_client.indices.delete(index=index_name, ignore=[400, 400])
    assert await es_client.indices.exists(index=index_name) == False

