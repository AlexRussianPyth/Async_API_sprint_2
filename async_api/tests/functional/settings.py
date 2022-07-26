from pydantic import BaseSettings, Field


class TestSettings(BaseSettings):
    es_host: str = Field('http://127.0.0.1', env='ES_HOST')
    es_port: str = Field('9200', env='ES_PORT')

    redis_host: str = Field('127.0.0.1', env='REDIS_HOST')
    redis_port: str = Field('6379', env='REDIS_PORT')

    fastapi_host: str = Field('http://127.0.0.1', env='FASTAPI_HOST')
    fastapi_port: str = Field('8000', env='FASTAPI_PORT')
    default_page_size: int = Field(50, env='PAGE_SIZE')

    person_router_prefix: str = Field('/api/v1/persons', env='PERSON_ROUTER_PREFIX')
    movies_router_prefix: str = Field('/api/v1/films', env='MOVIES_ROUTER_PREFIX')


test_settings = TestSettings()
