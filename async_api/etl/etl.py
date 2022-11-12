import logging
import time

from schemas.es_index import (es_films_index_schema, es_genres_index_schema,
                              es_persons_index_schema)
from es_loader import EsLoader
from extractors import FilmExtractor, GenreExtractor, PersonExtractor
from core.settings import es_settings, postgre_settings
from state import JsonFileStorage, State
from transformers import (transform_film_record, transform_genre_record,
                          transform_person_record)
from db.connections import create_pg_conn


logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger('etl_logger')

WAIT_SEC = 2


if __name__ == '__main__':
    with create_pg_conn(postgre_settings.dict()) as pg_conn:
        # Запускаем класс, управляющий записями о состояниях
        json_storage = JsonFileStorage('states.json')
        json_storage.create_json_storage()
        state = State(json_storage)

        # Подключаем классы, управляющие выгрузкой данных из Postgre
        film_extractor = FilmExtractor(pg_conn, state)
        genre_extractor = GenreExtractor(pg_conn)
        person_extractor = PersonExtractor(pg_conn)

        # Подключимся к нашему Elastic Search серверу
        loader = EsLoader(address=es_settings.get_full_address())

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
