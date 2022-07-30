import os
import pathlib

from logging import config as logging_config
from dotenv import load_dotenv
from pydantic import BaseSettings, Field

from core.logger import LOGGING

load_dotenv(os.path.join(pathlib.Path(__file__).parent.parent.parent.absolute(), '.env'))


class MainSettings(BaseSettings):
    class Config:
        env_file = '../.env'
        env_file_encoding = 'utf-8'


class ApiSettings(MainSettings):
    uvicorn_reload: bool = Field(..., env='UVICORN_RELOAD')
    project_name: str = Field(..., env='PROJECT_NAME')
    page_size: int = Field(..., env='PAGE_SIZE')
    language: str = Field(..., env='LOC_LANGUAGE')


class DatabaseSettings(MainSettings):
    redis_host: str = Field(..., env='REDIS_HOST')
    redis_port: int = Field(..., env='REDIS_PORT')
    elastic_host: str = Field(..., env='ELASTIC_HOST')
    elastic_port: int = Field(..., env='ELASTIC_PORT')


class CacheSettings(MainSettings):
    genre_cache_expire_sec: int = Field(..., env='GENRE_CACHE_EXPIRE_IN_SECONDS')
    person_cache_expire_sec: int = Field(..., env='PERSON_CACHE_EXPIRE_IN_SECONDS')
    film_cache_expire_sec: int = Field(..., env='FILM_CACHE_EXPIRE_IN_SECONDS')


db_settings = DatabaseSettings()
cache_settings = CacheSettings()
api_settings = ApiSettings()


# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))