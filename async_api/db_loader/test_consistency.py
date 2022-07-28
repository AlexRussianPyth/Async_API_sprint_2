import os
import pathlib

import psycopg2
from db_settings import POSTGRE_SETTINGS, SQLITE_DB
from load_data import sqlite_conn_context_manager
from psycopg2.extras import DictCursor

sqlite_db_path = os.path.join(pathlib.Path(__file__).parent.absolute(), SQLITE_DB)


def test_check_magnitude_equality():
    with sqlite_conn_context_manager(sqlite_db_path) as sqlite_conn, psycopg2.connect(
            **POSTGRE_SETTINGS, cursor_factory=DictCursor) as pg_conn:

        table_names = ['film_work', 'person', 'genre', 'person_film_work', 'genre_film_work']

        for table_name in table_names:
            sqlite_curs = sqlite_conn.cursor()
            sqlite_curs.execute(f'SELECT COUNT(1) FROM {table_name}')
            sqlite_rows = sqlite_curs.fetchone()[0]

            pg_curs = pg_conn.cursor()
            pg_curs.execute(f'SELECT COUNT(1) FROM content.{table_name}')
            pg_rows = pg_curs.fetchone()[0]

            assert sqlite_rows == pg_rows
