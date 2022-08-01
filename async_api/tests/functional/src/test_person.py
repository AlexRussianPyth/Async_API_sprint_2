from http import HTTPStatus

import pytest
from elasticsearch._async.helpers import async_bulk

from tests.functional.testdata.es_index import es_persons_index_schema
from tests.functional.testdata.persons_data import es_persons

pytestmark = pytest.mark.asyncio


async def test_person_by_id(es_client, make_get_request):
    # Создание и заполнение индекса в Elastic
    await es_client.indices.create(index='person_test', body=es_persons_index_schema, ignore=400)
    persons = [{"_index": 'person_test', "_id": obj.get("id"), **obj} for obj in es_persons]
    await async_bulk(client=es_client, actions=persons)

    response = await make_get_request(endpoint=f"persons/{es_persons[0]['id']}")
    assert response.status == HTTPStatus.OK
    print(response.body)




