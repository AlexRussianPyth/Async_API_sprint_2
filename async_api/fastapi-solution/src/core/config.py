import os
from enum import Enum
from logging import config as logging_config

from core.logger import LOGGING
from pydantic import BaseSettings, Field


class Language(Enum):
    """Описывает те языки, которые есть в наличии для нашего API"""
    RU = 'RU'
    EN = 'EN'


class MainSettings(BaseSettings):
    class Config:
        env_file_encoding = 'utf-8'
        use_enum_values = True


class ApiSettings(MainSettings):
    uvicorn_reload: bool = Field(..., env='UVICORN_RELOAD')
    project_name: str = Field(..., env='PROJECT_NAME')
    page_size: int = Field(..., env='PAGE_SIZE')
    language: Language = Field(..., env='LOC_LANGUAGE')
    jwt_secret: str = Field(..., env='JWT_SECRET')
    jwt_algorithm: str = Field(..., env='JWT_ALGORITHM')


class DatabaseSettings(MainSettings):
    redis_host: str = Field(..., env='REDIS_HOST')
    redis_port: int = Field(..., env='REDIS_PORT')
    elastic_host: str = Field(..., env='ES_HOST')
    elastic_port: int = Field(..., env='ES_PORT')


class CacheSettings(MainSettings):
    genre_cache_expire_sec: int = Field(..., env='GENRE_CACHE_EXPIRE_IN_SECONDS')
    person_cache_expire_sec: int = Field(..., env='PERSON_CACHE_EXPIRE_IN_SECONDS')
    film_cache_expire_sec: int = Field(..., env='FILM_CACHE_EXPIRE_IN_SECONDS')


class SentrySettings(MainSettings):
    sentry_dsn: str
    sentry_traces_sample_rate: float = 1.0


db_settings = DatabaseSettings()
cache_settings = CacheSettings()
api_settings = ApiSettings()
sentry_settings = SentrySettings()

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
