import random
from http import HTTPStatus

import pytest
from async_api.tests.functional.settings import test_settings

from async_api.tests.functional.testdata.persons_data import es_persons

pytestmark = pytest.mark.asyncio


async def test_person_by_id(es_client, make_get_request, persons_index):
    """Поиск конкретного человека"""

    es_person = random.choice(es_persons)
    response = await make_get_request(endpoint=f"{test_settings.person_router_prefix}/{es_person['id']}")
    assert response.status == HTTPStatus.OK
    api_person = response.body

    assert es_person['id'] == api_person['uuid']
    assert es_person['full_name'] == api_person['full_name']
    assert es_person['role'] == api_person['role']


async def test_films_by_person(es_client, make_get_request, persons_index):
    """Поиск всех фильмов с участием человека"""
    es_person = random.choice(es_persons)
    response = await make_get_request(endpoint=f"{test_settings.person_router_prefix}/{es_person['id']}/film")
    assert response.status == HTTPStatus.OK
    api_person = response.body
    print(api_person)
    # TODO сделать проверку фильмов


async def test_all_persons(es_client, make_get_request, persons_index):
    """Вывод всех людей"""

    response = await make_get_request(endpoint=f'{test_settings.person_router_prefix}/search')
    assert response.status == HTTPStatus.OK
    api_persons = response.body
    print(api_persons)
    assert len(es_persons) == len(api_persons)
    for es_person in es_persons:
        assert next(filter(lambda person: person['uuid'] == es_person['id'], api_persons))

# TODO поиск с учётом кеша в Redis - Делать запрос и проверять, что в редисе лежит ответ
