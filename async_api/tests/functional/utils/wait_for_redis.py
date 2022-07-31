import logging
import sys
import time
import asyncio

import aioredis

# setting path
sys.path.append('..')

from settings import test_settings

logger = logging.getLogger('tests_logger')

HOST = test_settings.redis_host
PORT = test_settings.redis_port


async def redis_connection_checker(host: str, port: str) -> bool:
    client = await aioredis.create_redis_pool(address=(host, port), minsize=10, maxsize=20)
    if await client.ping() == b'PONG':
        logger.info('Redis Работает')
        return True
    logger.info('Ожидаем соединения с Redis')
    return False

if __name__ == '__main__':
    while True:
        if asyncio.run(redis_connection_checker(HOST, PORT)):
            break
        else:
            time.sleep(2)
