import asyncio
import logging
import sys

import elasticsearch
from backoff import backoff

# setting path
sys.path.append('..')

from settings import test_settings

HOST = test_settings.es_host

logger = logging.getLogger()
client = elasticsearch.AsyncElasticsearch(hosts=HOST)


@backoff()
async def elastic_connection_checker(es):
    """Проверяет наличие соединения с Эластиком. Если оно найдено - возвращает True и закрывает соединение"""
    if await es.ping():
        logger.info('Соединение с ES установлено')
        await es.close()
        return True
    logger.info('Ожидаем соединения с ES')
    return False


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(elastic_connection_checker(client))
    loop.close()
