import pytest
from http import HTTPStatus
from uuid import UUID
from ..settings import test_settings
from ..utils.cache import generate_cache_key

from pydantic import BaseModel


class PersonShortInfo(BaseModel):
    id: str
    name: str

class FilmSchema(BaseModel):
    """Полный набор полей для эндпоинта с описанием одного фильма"""
    uuid: UUID
    title: str
    imdb_rating: float
    genre: list[str] | None
    description: str | None
    directors: list[str] | None
    actors: list[PersonShortInfo] | None
    writers: list[PersonShortInfo] | None

# ПОИСК ПО ФИЛЬМАМ
@pytest.mark.asyncio
async def test_search_films(es_client, redis_client, make_get_request, movies_index):
    """Проверяет работу поиска по фильмам"""
    await redis_client.flushall()
    # Выполняем поисковый запрос
    response = await make_get_request(
        endpoint='/api/v1/films/search',
        params={'query': 'Disney'}
    )

    assert response.status == HTTPStatus.OK
    assert len(response.body) == 4
    # Проверяем, что схемы верны
    for film in response.body:
        assert FilmSchema(**film) # TODO Так себе проверка?

    # проверяем кэширование


# ПОИСК ПО ПЕРССОНАМ



