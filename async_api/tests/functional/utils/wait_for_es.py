import logging
import time
import sys

# setting path
sys.path.append('..')

from elasticsearch import AsyncElasticsearch
import asyncio

from settings import test_settings


HOST = test_settings.es_host
# HOST = '127.0.0.1:9200'

logger = logging.getLogger('tests_logger')
client = AsyncElasticsearch(hosts=HOST)


async def elastic_connection_checker(es):
    """Проверяет наличие соединения с Эластиком. Если оно найдено - возвращает True и закрывает соединение"""
    if await es.ping():
        logger.warning('ES Работает')
        await es.close()
        return True
    else:
        logger.warning('Ожидаем соединения с ES')
        return False

if __name__ == '__main__':
    while True:
        if asyncio.run(elastic_connection_checker(client)):
            break
        else:
            time.sleep(2)
