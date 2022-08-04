import asyncio
import json
import random
from http import HTTPStatus
from uuid import UUID

import pytest
from elasticsearch._async.helpers import async_bulk
from elasticsearch.exceptions import NotFoundError
from pydantic import BaseModel

from testdata.genres_data import es_genres
from utils.cache import generate_cache_key
from testdata.es_index import es_genres_index_schema

index_name = 'genres'


class GenreApiScheme(BaseModel):
    """Модель для валидации данных жанра от api"""
    uuid: UUID
    name: str


@pytest.mark.asyncio
async def test_genre_index_creation(es_client, redis_client):
    """Проверяет, можно процесс создания индекса в Эластике"""
    # Сбросим кэш Рэдиса
    await redis_client.flushall()
    # Создаем индекс, если в Эластике нет индекса с заданным именем
    if not await es_client.indices.exists(index=index_name):
        await es_client.indices.create(index=index_name, ignore=400, body=es_genres_index_schema)
    # Проверяем наличие вновь созданного индекса
    assert await es_client.indices.exists(index=index_name), f"Индекс с заданным именем {index_name} не был создан"


@pytest.mark.asyncio
async def test_add_genres_docs(es_client, redis_client, make_get_request):
    """Проверяет, что жанры правильно добавляются в созданный индекс"""
    cache_key = await generate_cache_key(index='genres', query=None, page=1)
    assert await redis_client.get(key=cache_key) is None
    # Добавляем жанры в индекс
    genres = [{"_index": index_name, "_id": obj.get("id"), **obj} for obj in es_genres]
    await async_bulk(client=es_client, actions=genres)

    # Проверяем код ответа и количество документов
    await asyncio.sleep(1)  # ждем чтобы индекс успел обновиться
    response = await make_get_request(endpoint="/api/v1/genres/")
    assert response.status == HTTPStatus.OK
    assert(len(response.body)) == len(genres), f'Количество добавленных жанров не равно запланированным {len(genres)}'

    # Проверяем, что мы не находим документы по несуществующим id
    with pytest.raises(NotFoundError):
        await es_client.get(index='genres', id='not-resalistic-id')

    # Валидируем полученные жанры
    assert all([GenreApiScheme(**genre) for genre in response.body])


@pytest.mark.asyncio
async def test_get_genre_by_id(es_client, redis_client, make_get_request):
    """Проверяем получение одного жанра по id"""
    await redis_client.flushall()
    # Выбираем случайный id из загруженных жанров
    es_genre = random.choice(es_genres)

    # Проверяем, что этого жанра нет в кэше
    assert await redis_client.get(key=es_genre['id']) is None

    # Получаем жанр
    response = await make_get_request(endpoint=f"/api/v1/genres/{es_genre['id']}")

    # Проверяем полученный жанр
    assert response.status == HTTPStatus.OK
    genre = GenreApiScheme(**response.body)
    assert es_genre['id'] == str(genre.uuid)
    assert es_genre['name'] == genre.name

    # Проверяем верность закешированной информации о жанре
    cache_genre_json = await redis_client.get(key=es_genre['id'])
    assert cache_genre_json
    cache_genre = json.loads(cache_genre_json)
    assert isinstance(cache_genre, dict)
    assert es_genre['id'] == cache_genre.get('id')
    assert es_genre['name'] == cache_genre.get('name')


@pytest.mark.asyncio
async def test_genre_index_deletion(es_client):
    """Проверяем, что индекс возможно верно удалить"""
    # Удаляем индекс
    await es_client.indices.delete(index=index_name, ignore=[400, 400])
    # Проверяем, что индекс с заданным именем больше не существует
    assert await es_client.indices.exists(index=index_name) == False
