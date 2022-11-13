import logging

from core.backoff import backoff
from psycopg2.extensions import connection as _connection
from core.utils import ornate_ids


class FilmExtractor:
    """Получает из Postgre обновленные записи фильмов, людей, жанров, в то же время
    обогащает их связанными данными"""
    def __init__(self, connection: _connection, state_manager):
        self.connection = connection
        self.state_manager = state_manager

    @backoff()
    def execute_query(self, query: str):
        curs = self.connection.cursor()
        curs.execute(query)
        return curs

    @backoff()
    def extract_data(self, batch_size=100):
        """Проходит по всем данным в таблицах
        Returns: Список измененных фильмов со всеми связанными данными о людях и жанрах
        """
        last_film_check = self.state_manager.get_state("last_film_work_check")
        last_genre_check = self.state_manager.get_state("last_genre_check")
        last_person_check = self.state_manager.get_state("last_person_check")

        if last_film_check <= last_person_check and last_film_check <= last_genre_check:
            films = self.get_modified(table="film_work", date=last_film_check, batch_size=batch_size)
        elif last_person_check <= last_genre_check:
            persons = self.get_modified(table="person", date=last_person_check, batch_size=batch_size)
            films = self.find_person_film_connection(persons)
        else:
            genres = self.get_modified(table="genre", date=last_genre_check, batch_size=batch_size)
            films = self.find_genre_film_connection(genres)

        if len(films) == 0:
            logging.debug('В Postgre нет данных, которые следует отправить в Elastic')
            return []

        # Если актуальные фильмы существуют, то функция денормализует их
        full_data = self.enrich_modified_films(films)
        return full_data

    @backoff()
    def get_modified(self, table: str, date: str, batch_size: int) -> list[list]:

        query = f'''
        SELECT id, modified
        FROM content.{table}
        WHERE modified > '{date}'
        ORDER BY modified
        LIMIT {batch_size};
        '''

        curs = self.execute_query(query)
        query_result = curs.fetchall()

        # Если данных в запросе нет, то возвращаем пустой лист
        if len(query_result) == 0:
            return []

        # Изменяем дату состояния так, чтобы она соответствовала самому большому значению 'modified' из пачки
        self.state_manager.set_state(key=f'last_{table}_check', value=str(query_result[-1][1]))

        # возвращаем пачку DictRows
        return query_result

    @backoff()
    def find_person_film_connection(self, modified_persons):

        person_ids = [obj['id'] for obj in modified_persons]
        id_string = ornate_ids(person_ids)

        query = f"""
        SELECT fw.id, fw.modified
        FROM content.film_work AS fw
        LEFT JOIN content.person_film_work AS pfw ON pfw.film_work_id = fw.id
        WHERE pfw.person_id IN ({id_string})
        ORDER BY fw.modified;
        """

        curs = self.execute_query(query)
        films = curs.fetchall()

        return films

    @backoff()
    def find_genre_film_connection(self, modified_genres):

        genre_ids = [obj['id'] for obj in modified_genres]
        id_string = ornate_ids(genre_ids)

        query = f"""
        SELECT fw.id, fw.modified
        FROM content.film_work AS fw
        LEFT JOIN content.genre_film_work AS gfw ON gfw.film_work_id = fw.id
        WHERE gfw.genre_id IN ({id_string})
        ORDER BY fw.modified;
        """

        curs = self.execute_query(query)
        films = curs.fetchall()

        return films

    @backoff()
    def enrich_modified_films(self, modified_films: list[list]) -> list[list]:

        films_ids = [obj['id'] for obj in modified_films]
        id_string = ornate_ids(films_ids)

        query = f"""
        SELECT fw.id as filmwork_id, fw.title, fw.description, fw.subscription, fw.rating,
               ARRAY_AGG(DISTINCT g.name) AS genre,
               ARRAY_AGG(DISTINCT p.full_name) FILTER (WHERE pfw.role = 'director') AS director,
               ARRAY_AGG(DISTINCT p.full_name) FILTER (WHERE pfw.role = 'actor') AS actors_names,
               ARRAY_AGG(DISTINCT p.full_name) FILTER (WHERE pfw.role = 'writer') AS writers_names,
               ARRAY_AGG(DISTINCT p.id || '|' || p.full_name) FILTER (WHERE pfw.role = 'actor') AS actors,
               ARRAY_AGG(DISTINCT p.id || '|' || p.full_name) FILTER (WHERE pfw.role = 'writer') AS writers
        FROM content.film_work AS fw
        LEFT JOIN content.person_film_work AS pfw ON pfw.film_work_id = fw.id
        LEFT JOIN content.person AS p ON p.id = pfw.person_id
        LEFT JOIN content.genre_film_work AS gfw ON gfw.film_work_id = fw.id
        LEFT JOIN content.genre AS g ON g.id = gfw.genre_id
        WHERE fw.id IN ({id_string})
        GROUP BY fw.id;
        """

        curs = self.execute_query(query)
        enriched_films = curs.fetchall()

        return enriched_films


class GenreExtractor:
    """Вытаскивает из Postgre обновленные записи по жанрам"""
    def __init__(self, connection: _connection):
        self.connection = connection

    @backoff()
    def execute_query(self, query: str):
        curs = self.connection.cursor()
        curs.execute(query)
        return curs

    @backoff()
    def extract_genres(self):

        query = '''
                SELECT id, name
                FROM content.genre;
                '''

        curs = self.execute_query(query)
        query_result = curs.fetchall()

        # Если данных в запросе нет, то возвращаем пустой лист
        if len(query_result) == 0:
            return []

        return query_result


class PersonExtractor:
    """Вытаскивает из Postgre обновленные записи по жанрам"""
    def __init__(self, connection: _connection):
        self.connection = connection

    @backoff()
    def execute_query(self, query: str):
        curs = self.connection.cursor()
        curs.execute(query)
        return curs

    @backoff()
    def extract_persons(self):

        query = '''
                SELECT p.id, p.full_name, pfw.role
                FROM content.person as p
                INNER JOIN content.person_film_work as pfw ON pfw.person_id = p.id;
                '''

        curs = self.execute_query(query)
        query_result = curs.fetchall()

        # Если данных в запросе нет, то возвращаем пустой лист
        if len(query_result) == 0:
            return []

        return query_result
