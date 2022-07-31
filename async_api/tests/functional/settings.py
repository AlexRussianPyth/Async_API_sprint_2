from pydantic import BaseSettings, Field


class TestSettings(BaseSettings):
    es_host: str = Field('http://127.0.0.1', env='ES_HOST')
    es_port: str = Field('9200', env='ES_PORT')

    redis_host: str = Field('127.0.0.1', env='REDIS_HOST')
    redis_port: str = Field('6379', env='REDIS_PORT')

    class Config:
        env_file = '../.env'
        env_file_encoding = 'utf-8'


test_settings = TestSettings()
