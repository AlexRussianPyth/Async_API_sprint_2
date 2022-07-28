import datetime
import sqlite3
from typing import Dict, List

from movie_dataclasses import (FilmWork, Genre, GenreFilmWork, Person,
                               PersonFilmWork)
from psycopg2.extensions import AsIs
from psycopg2.extensions import connection as _connection
from psycopg2.extras import execute_batch


class SQLiteLoader:
    def __init__(self, sql_conn: sqlite3.Connection, batch_size: int):
        self.sql_conn = sql_conn
        self.batch_size = batch_size

    def execute(self, query: str):
        curs = self.sql_conn.cursor()
        curs.execute(query)
        return curs

    def load_movies(self):
        sqlite_films_gen = self.__load_filmworks()
        sqlite_persons_gen = self.__load_persons()
        sqlite_genres_gen = self.__load_genres()
        sqlite_person_film_m2m_gen = self.__load_persons_films_m2m()
        sqlite_genre_film_m2m_gen = self.__load_genres_films_m2m()

        data_generators = [
            sqlite_films_gen,
            sqlite_persons_gen,
            sqlite_genres_gen,
            sqlite_person_film_m2m_gen,
            sqlite_genre_film_m2m_gen
            ]

        return data_generators

    def __load_filmworks(self):
        query = 'SELECT * FROM film_work;'
        curs = self.execute(query)

        while rows := curs.fetchmany(size=self.batch_size):
            film_data = [FilmWork(**obj) for obj in rows]
            yield {'type': 'films_data', 'objects': film_data}

    def __load_persons(self):
        query = 'SELECT * FROM person;'
        curs = self.execute(query)

        while rows := curs.fetchmany(size=self.batch_size):
            person_data = [Person(**obj) for obj in rows]
            yield {'type': 'persons_data', 'objects': person_data}

    def __load_genres(self):
        query = 'SELECT * FROM genre;'
        curs = self.execute(query)

        while rows := curs.fetchmany(size=self.batch_size):
            genre_data = [Genre(**obj) for obj in rows]
            yield {'type': 'genres_data', 'objects': genre_data}

    def __load_persons_films_m2m(self):
        query = 'SELECT * FROM person_film_work;'
        curs = self.execute(query)

        while rows := curs.fetchmany(size=self.batch_size):
            person_film_data = [PersonFilmWork(**obj) for obj in rows]
            yield {'type': 'person_films_data', 'objects': person_film_data}

    def __load_genres_films_m2m(self):
        query = 'SELECT * FROM genre_film_work;'
        curs = self.execute(query)

        while rows := curs.fetchmany(size=self.batch_size):
            genre_film_data = [GenreFilmWork(**obj) for obj in rows]
            yield {'type': 'genre_films_data', 'objects': genre_film_data}


class PostgresSaver:
    def __init__(self, pg_conn: _connection):
        self.pg_conn = pg_conn

    def execute(self, query: str, values: List[tuple]):
        curs = self.pg_conn.cursor()
        execute_batch(curs, query, values)
        curs.close()

    @staticmethod
    def date_checker(date: str) -> str:
        if date is None or date in ('Null', 'None'):
            return str(datetime.datetime.now().date())
        return date

    @staticmethod
    def text_to_pg_format(text: str) -> str:
        return text.replace("'", "''")

    @staticmethod
    def rating_checker(rating: str) -> str:
        if rating is None or rating == 'None':
            return '0.0'
        return rating

    def __save_film_work_to_db(self, film_work_data: List[FilmWork]):
        query = '''INSERT INTO content.film_work (id, title, description,
                creation_date, rating, type, created, modified) VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)'''

        values = []

        for film in film_work_data:
            value = (
                str(film.id),
                self.text_to_pg_format(str(film.title)),
                self.text_to_pg_format(str(film.description)),
                self.date_checker(str(film.creation_date)),
                self.rating_checker(str(film.rating)),
                str(film.type),
                self.date_checker(str(film.created_at)),
                self.date_checker(str(film.updated_at)),
                )
            values.append(value)

        self.execute(query, values)

    def __save_persons_to_db(self, persons_data: List[Person]):
        query = '''INSERT INTO content.person (id, full_name, created, modified)
                VALUES (%s, %s, %s, %s)'''

        values = []

        for person in persons_data:
            value = (
                str(person.id),
                self.text_to_pg_format(str(person.full_name)),
                self.date_checker(str(person.created_at)),
                self.date_checker(str(person.updated_at)),
            )
            values.append(value)

        self.execute(query, values)

    def __save_genres_to_db(self, genres_data: List[Genre]):
        query = '''INSERT INTO content.genre (id, name, description, created, modified)
                VALUES (%s, %s, %s, %s, %s)'''

        values = []

        for genre in genres_data:
            value = (
                str(genre.id),
                self.text_to_pg_format(str(genre.name)),
                self.text_to_pg_format(str(genre.description)),
                self.date_checker(str(genre.created_at)),
                self.date_checker(str(genre.updated_at)),
                )
            values.append(value)

        self.execute(query, values)

    def __save_person_film_m2m_to_db(self, person_film_m2m_data: List[PersonFilmWork]):
        query = '''INSERT INTO content.person_film_work (id, person_id,
                film_work_id, role, created)
                VALUES (%s, %s, %s, %s, %s)'''

        values = []

        for relation in person_film_m2m_data:
            value = (
                str(relation.id),
                str(relation.person_id),
                str(relation.film_work_id),
                self.text_to_pg_format(str(relation.role)),
                self.date_checker(str(relation.created_at)),
                )
            values.append(value)

        self.execute(query, values)

    def __save_genre_film_m2m_to_db(self, genre_film_m2m_data: List[GenreFilmWork]):
        query = '''INSERT INTO content.genre_film_work (id, genre_id, film_work_id, created)
                VALUES (%s, %s, %s, %s)'''

        values = []

        for relation in genre_film_m2m_data:
            value = (
                str(relation.id),
                str(relation.genre_id),
                str(relation.film_work_id),
                self.date_checker(str(relation.created_at)),
                )
            values.append(value)

        self.execute(query, values)

    def save_batch(self, data: Dict):

        type_selector = {
            'films_data': self.__save_film_work_to_db,
            'persons_data': self.__save_persons_to_db,
            'genres_data': self.__save_genres_to_db,
            'person_films_data': self.__save_person_film_m2m_to_db,
            'genre_films_data': self.__save_genre_film_m2m_to_db,
        }

        batch_type = data['type']

        saving_method = type_selector[batch_type]
        saving_method(data['objects'])

    def clear_all_data(self):
        SCHEMA = 'content'

        tables = (
            'film_work',
            'person',
            'genre',
            'person_film_work',
            'genre_film_work'
        )

        for table in tables:
            self.execute('TRUNCATE %s.%s CASCADE;', [(AsIs(SCHEMA), AsIs(table))])
