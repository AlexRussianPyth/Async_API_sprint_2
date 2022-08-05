import json
import random
from http import HTTPStatus
from uuid import UUID

import pytest
from pydantic import BaseModel

from settings import test_settings

pytestmark = pytest.mark.asyncio


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


async def test_movie_by_id(es_client, make_get_request, redis_client, movies_index, get_films):
    """Поиск конкретного фильма"""

    films = get_films(FilmSchema)
    film = random.choice(films)
    await redis_client.flushall()
    assert await redis_client.get(key=str(film.uuid)) is None

    response = await make_get_request(endpoint=f"{test_settings.movies_router_prefix}/{film.uuid}")
    assert response.status == HTTPStatus.OK
    api_film = FilmSchema(**response.body)
    assert api_film.dict() == film.dict()

    cache_film_json = await redis_client.get(key=str(film.uuid))
    assert cache_film_json
    cache_film = json.loads(cache_film_json)
    assert isinstance(cache_film, dict)
    cache_model_film = FilmSchema(**cache_film, uuid=cache_film['id'], directors=cache_film['director'])
    assert cache_model_film.dict() == film.dict()
