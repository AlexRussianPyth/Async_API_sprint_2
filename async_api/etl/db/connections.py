import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor

from core.backoff import backoff


@backoff()
def create_pg_conn(settings: dict) -> _connection:
    """Создает подключение к Postgre"""
    return psycopg2.connect(**settings, cursor_factory=DictCursor)
