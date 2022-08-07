import asyncio
import logging
import sys
import time

import aioredis

# setting path
sys.path.append('..')

from settings import test_settings
from backoff import backoff

logger = logging.getLogger()


@backoff()
async def redis_connection_checker(host: str, port: str) -> bool:
    client = await aioredis.create_redis_pool(address=(host, port), minsize=10, maxsize=20)
    if await client.ping() == b'PONG':
        logger.info('Redis Работает')
        return True
    logger.info('Ожидаем соединения с Redis')
    return False


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(redis_connection_checker(test_settings.redis_host, test_settings.redis_port))
    loop.close()
