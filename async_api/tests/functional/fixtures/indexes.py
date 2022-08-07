import json

import pytest
from elasticsearch._async.helpers import async_bulk
from testdata.es_index import es_films_index_schema, es_persons_index_schema
from testdata.persons_data import es_persons


@pytest.fixture(scope='session')
async def persons_index(es_client):
    """Создание и заполнение индекса в Elastic"""

    index_name = 'persons'
    await es_client.indices.create(index=index_name, body=es_persons_index_schema, ignore=400)
    persons = [{"_index": index_name, "_id": obj.get("id"), **obj} for obj in es_persons]
    await async_bulk(client=es_client, actions=persons)
    await es_client.indices.refresh(index=[index_name, ])

    yield

    await es_client.indices.delete(index=index_name)


@pytest.fixture(scope='session')
async def movies_index(es_client):
    """Создание и заполнение индекса в Elastic"""

    index_name = 'movies'
    await es_client.indices.create(index=index_name, body=es_films_index_schema, ignore=400)
    with open('./testdata/movies.json') as file:
        es_films = json.load(file)
    films = []
    for es_film in es_films:
        film = {
            "_index": index_name,
            "_id": es_film.get("id"),
            "id": es_film.get("id"),
            "title": es_film.get("title"),
            "description": es_film.get("description"),
            "imdb_rating": es_film.get("imdb_rating"),
            "genre": es_film.get("genre"),
            "actors": es_film.get("actors"),
            "writers": es_film.get("writers"),
            "actors_names": es_film.get("actors_names"),
            "writers_names": es_film.get("writers_names"),
            "director": es_film.get("director"),

        }
        films.append(film)
    await async_bulk(client=es_client, actions=films)
    await es_client.indices.refresh(index=[index_name, ])

    yield

    await es_client.indices.delete(index=index_name)


@pytest.fixture(scope='session')
def get_films():
    def inner(schema):
        with open('./testdata/movies.json') as file:
            es_films = json.load(file)
        return [schema(**es_film, uuid=es_film['id'], directors=es_film['director']) for es_film in es_films]

    return inner
