import pytest


# TODO Доработать этот тест, он из примера в теории ЯП
@pytest.mark.skip(reason='Not realised yet')
@pytest.mark.asyncio
async def test_search_detailed(es_client, make_get_request):
    # Заполнение данных для теста
    await es_client.bulk(...)

    # Выполнение запроса
    response = await make_get_request('/search', {'search': 'Star Wars'})

    # Проверка результата
    assert response.status == 200
    assert len(response.body) == 1

    assert response.body == expected
