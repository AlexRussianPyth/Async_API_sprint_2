from pydantic import BaseSettings, Field


class EnvMixin(BaseSettings):
    """
    Благодаря этому миксину мы можем легко подключить переменные окружения
    """
    class Config:
        env_file = '../.env'
        env_file_encoding = 'utf-8'


class PostgreSettings(EnvMixin, BaseSettings):
    """
    Настройки подключения к БД Postgres
    """
    database: str = Field(..., env='POSTGRES_DB')
    user: str = Field(..., env='POSTGRES_USER')
    password: str = Field(..., env='POSTGRES_PASSWORD')
    host: str = Field(..., env='DB_HOST')
    port: str = Field(..., env='DB_PORT')


class EsSettings(EnvMixin, BaseSettings):
    """
    Настройки подключения к Elastic Search
    """
    elastic_protocol: str = Field(..., env='ES_PROTOCOL')
    elastic_host: str = Field(..., env='ES_HOST')
    elastic_port: str = Field(..., env='ES_PORT')

    def get_full_address(self):
        """Позволяет получить полный URL адрес для подключения к Elastic"""
        return self.elastic_protocol + '://' + self.elastic_host + ':' + self.elastic_port


# Инициализируем объекты с настройками
postgre_settings = PostgreSettings()
es_settings = EsSettings()
