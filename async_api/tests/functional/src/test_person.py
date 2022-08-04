import json
import random
from http import HTTPStatus
from uuid import UUID

import pytest
from pydantic import BaseModel

from settings import test_settings
from testdata.persons_data import es_persons
from utils.cache import generate_cache_key

pytestmark = pytest.mark.asyncio


class PersonBase(BaseModel):
    """Базовый набор полей персоны"""
    full_name: str
    role: str


class PersonScheme(PersonBase):
    """Модель для валидации данных персоны от api"""
    uuid: UUID
    film_ids: list[str]


class PersonModel(PersonBase):
    """Модель для валидации данных персоны из кеша"""
    id: str
    films_ids: list[str]


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


async def test_person_by_id(es_client, make_get_request, redis_client, persons_index):
    """Поиск конкретного человека"""

    es_person = random.choice(es_persons)
    await redis_client.flushall()
    assert await redis_client.get(key=es_person['id']) is None

    response = await make_get_request(endpoint=f"{test_settings.person_router_prefix}/{es_person['id']}")
    assert response.status == HTTPStatus.OK
    person = PersonScheme(**response.body)
    assert es_person['id'] == str(person.uuid)
    assert es_person['full_name'] == person.full_name
    assert es_person['role'] == person.role

    cache_person_json = await redis_client.get(key=es_person['id'])
    assert cache_person_json
    cache_person = json.loads(cache_person_json)
    assert isinstance(cache_person, dict)
    assert es_person['id'] == cache_person.get('id')
    assert es_person['full_name'] == cache_person.get('full_name')
    assert es_person['role'] == cache_person.get('role')


async def test_films_by_person(es_client, make_get_request, persons_index):
    """Поиск всех фильмов с участием человека"""

    es_person = random.choice(es_persons)
    response = await make_get_request(endpoint=f"{test_settings.person_router_prefix}/{es_person['id']}/film")
    assert response.status == HTTPStatus.OK
    films = response.body
    assert all([FilmSchema(**film) for film in films])


async def test_all_persons(es_client, make_get_request, redis_client, persons_index):
    """Вывод всех людей"""

    await redis_client.flushall()
    cache_key = generate_cache_key(index='persons', query=None, page=1)
    assert await redis_client.get(key=cache_key) is None

    response = await make_get_request(endpoint=f'{test_settings.person_router_prefix}/search')
    assert response.status == HTTPStatus.OK
    api_persons = response.body
    assert len(es_persons) == len(api_persons)
    for es_person in es_persons:
        assert next(filter(lambda person: person['uuid'] == es_person['id'], api_persons))
    assert all([PersonScheme(**api_person) for api_person in api_persons])

    persons_json = await redis_client.get(cache_key)
    assert persons_json
    persons = json.loads(persons_json)
    assert isinstance(persons, list)
    assert all(PersonModel(**json.loads(person)) for person in persons)
