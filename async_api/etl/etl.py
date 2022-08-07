import logging
import time

import psycopg2
from backoff import backoff
from es_index import (es_films_index_schema, es_genres_index_schema,
                      es_persons_index_schema)
from es_loader import EsLoader
from extractors import FilmExtractor, GenreExtractor, PersonExtractor
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor
from settings import EsSettings, PostgreSettings
from state import JsonFileStorage, State
from transformers import (transform_film_record, transform_genre_record,
                          transform_person_record)

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger('etl_logger')

WAIT_SEC = 2


@backoff()
def create_pg_conn(settings: dict) -> _connection:
    """Создает подключение к Postgre"""
    return psycopg2.connect(**settings, cursor_factory=DictCursor)


if __name__ == '__main__':
    with create_pg_conn(PostgreSettings().dict()) as pg_conn:
        # Запускаем класс, управляющий записями о состояниях
        json_storage = JsonFileStorage('states.json')
        json_storage.create_json_storage()
        state = State(json_storage)

        # Подключаем классы, управляющие выгрузкой данных из Postgre
        film_extractor = FilmExtractor(pg_conn, state)
        genre_extractor = GenreExtractor(pg_conn)
        person_extractor = PersonExtractor(pg_conn)

        # Подключимся к нашему Elastic Search серверу
        es_settings = EsSettings()
        address = es_settings.get_full_address()

        # Инициализируем класс, который управляет загрузкой данных в ElasticSearch
        loader = EsLoader(address=address)

        # Проверяем наличие индекса и создаем его, если индекс отсутствует
        loader.create_index(index_name='movies', schema=es_films_index_schema)
        loader.create_index(index_name='genres', schema=es_genres_index_schema)
        loader.create_index(index_name='persons', schema=es_persons_index_schema)

        while True:
            films_data = film_extractor.extract_data()

            # Если скрипт не находит измененных данных, то мы ожидаем указанное количество времени и возобновляем поиск
            if films_data == []:
                logging.debug(f"Актуальных данных нет, спим {WAIT_SEC} секунд")
                time.sleep(WAIT_SEC)
                continue

            validated_data = transform_film_record(films_data)
            loader.bulk_upload(data=validated_data, index='movies', chunk_size=80)

            # Load Genres in Genre Index
            genre_data = genre_extractor.extract_genres()
            validated_genre_data = transform_genre_record(genre_data)
            loader.bulk_upload(data=validated_genre_data, index='genres', chunk_size=80)

            # Load Persons in Person Index
            person_data = person_extractor.extract_persons()
            validated_persons_data = transform_person_record(person_data)
            loader.bulk_upload(data=validated_persons_data, index='persons', chunk_size=80)
