import os
import pathlib

from dotenv import load_dotenv
from pydantic import BaseSettings, Field


load_dotenv(os.path.join(pathlib.Path(__file__).parent.absolute(), '.env'))


class TestSettings(BaseSettings):
    es_host: str = Field('http://127.0.0.1:9200', env='ES_HOST')

    class Config:
        env_file = '../.env'
        env_file_encoding = 'utf-8'


test_settings = TestSettings()
