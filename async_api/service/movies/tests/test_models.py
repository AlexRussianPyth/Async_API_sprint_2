import pytest
from django.db import connection


@pytest.mark.django_db
def test_database_creation():
    all_tables = connection.introspection.table_names()
    for table_name in ('genre', 'person', 'film_work', 'person_film_work', 'genre_film_work'):
        assert table_name in all_tables
