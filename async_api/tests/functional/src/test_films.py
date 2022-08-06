import json
import random
from http import HTTPStatus

import pytest

from settings import test_settings
from utils.cache import generate_cache_key
from utils.models import FilmSchema

pytestmark = pytest.mark.asyncio


async def test_movie_by_id(es_client, make_get_request, redis_client, movies_index, get_films):
    """Поиск конкретного фильма"""

    films = get_films(FilmSchema)
    film = random.choice(films)
    await redis_client.flushall()
    assert await redis_client.get(key=str(film.uuid)) is None

    response = await make_get_request(endpoint=f'{test_settings.movies_router_prefix}/{film.uuid}')
    assert response.status == HTTPStatus.OK
    api_film = FilmSchema(**response.body)
    assert api_film.dict() == film.dict()

    cache_film_json = await redis_client.get(key=str(film.uuid))
    assert cache_film_json
    cache_film = json.loads(cache_film_json)
    assert isinstance(cache_film, dict)
    cache_model_film = FilmSchema(**cache_film, uuid=cache_film['id'], directors=cache_film['director'])
    assert cache_model_film.dict() == film.dict()


async def test_all_movies(es_client, make_get_request, redis_client, movies_index):
    """Вывод страницы с фильмами"""

    await redis_client.flushall()
    page_size = 25
    cache_key = generate_cache_key(
        index="films",
        page=1,
        query=None,
        page_size=page_size,
        sort=None,
        filter_genre=None
    )
    assert await redis_client.get(key=cache_key) is None

    response = await make_get_request(endpoint=f'{test_settings.movies_router_prefix}/?page=1&page_size={page_size}')
    assert response.status == HTTPStatus.OK
    api_films = response.body
    assert len(api_films) == page_size
    assert all([FilmSchema(**api_film) for api_film in api_films])

    films_json = await redis_client.get(cache_key)
    assert films_json
    cache_films = json.loads(films_json)
    assert isinstance(cache_films, list)
    for cache_film in cache_films:
        decoded_film = json.loads(cache_film)
        assert FilmSchema(**decoded_film, uuid=decoded_film['id'], directors=decoded_film['director'])
