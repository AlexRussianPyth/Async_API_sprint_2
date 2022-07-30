from pydantic import BaseSettings, Field

# TODO Перенести настройки из переменных окружения
class TestSettings(BaseSettings):
    es_host: str = Field('http://127.0.0.1:9200', env='ELASTIC_HOST')