import json
from http import HTTPStatus

import pytest

from settings import test_settings
from utils.cache import generate_cache_key
from utils.models import PersonScheme, PersonModel, FilmSchema, FilmEsSchema


@pytest.mark.asyncio
async def test_films_search(es_client, redis_client, make_get_request, movies_index):
    """Проверяет работу поиска по фильмам"""
    await redis_client.flushall()

    # Выполняем поисковый запрос
    response = await make_get_request(
        endpoint=f'{test_settings.movies_router_prefix}/search',
        params={'query': 'Disney'}
    )
    assert response.status == HTTPStatus.OK
    assert len(response.body) == 4

    # Проверяем, что схемы верны и проходят валидацию
    search_result = []
    for film in response.body:
        validated_film = FilmSchema(**film)
        assert validated_film
        search_result.append(validated_film)

    # Проверяем кэширование
    cached_search_json = await redis_client.get(
        key=generate_cache_key(
            index='films',
            query='Disney',
            page=1,
            page_size=test_settings.default_page_size
        )
    )
    assert cached_search_json  # проверяем, что мы получили результат
    cached_search = [FilmEsSchema.parse_raw(film) for film in json.loads(cached_search_json)]
    assert isinstance(cached_search, list)

    # Проверяем, что закешированный результат равен результату, полученному из БД
    restored_films = [FilmSchema(uuid=film.id, directors=film.director, **film.dict()) for film in cached_search]
    assert search_result == restored_films


@pytest.mark.asyncio
async def test_person_search(es_client, redis_client, make_get_request, persons_index, movies_index):
    """Проверяет работу поиска по людям"""
    await redis_client.flushall()
    person_query_string = 'Devlin'

    # Выполняем поисковый запрос
    response = await make_get_request(
        endpoint=f'{test_settings.person_router_prefix}/search',
        params={'query': person_query_string}
    )

    assert response.status == HTTPStatus.OK
    assert len(response.body) == 1

    # Проверяем, что схемы верны и проходят валидацию
    search_result = []
    for person in response.body:
        validated_person = PersonScheme(**person)
        assert validated_person
        search_result.append(validated_person)

    # Проверяем кэширование
    cached_search_json = await redis_client.get(
        key=generate_cache_key(
            index='persons',
            query=person_query_string,
            page=1,
        )
    )

    assert cached_search_json  # проверяем, что мы получили результат
    cached_search = [PersonModel.parse_raw(person) for person in json.loads(cached_search_json)]
    assert isinstance(cached_search, list)

    # Проверяем, что закешированный результат равен результату, полученному из БД
    restored_persons = [PersonScheme(
        uuid=person.id,
        film_ids=person.films_ids,
        **person.dict()
    ) for person in cached_search]
    assert search_result == restored_persons
