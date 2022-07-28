import os
import pathlib
import sqlite3
from contextlib import contextmanager

import psycopg2
from db_settings import POSTGRE_SETTINGS, SQLITE_DB
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor
from transfer_to_psql import PostgresSaver, SQLiteLoader


@contextmanager
def sqlite_conn_context_manager(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def load_from_sqlite(connection: sqlite3.Connection, pg_conn: _connection):
    sqlite_loader = SQLiteLoader(connection, batch_size=30)
    postgres_saver = PostgresSaver(pg_conn)

    postgres_saver.clear_all_data()

    data_generators = sqlite_loader.load_movies()

    for data_generator in data_generators:
        while True:
            try:
                data = next(data_generator)
                postgres_saver.save_batch(data)
            except StopIteration:
                break


if __name__ == '__main__':
    sqlite_db_path = os.path.join(pathlib.Path(__file__).parent.absolute(), SQLITE_DB)
    with (
        sqlite_conn_context_manager(sqlite_db_path) as sqlite_conn,
        psycopg2.connect(**POSTGRE_SETTINGS, cursor_factory=DictCursor) as pg_conn
    ):
        load_from_sqlite(sqlite_conn, pg_conn)
