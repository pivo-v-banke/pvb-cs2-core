from celery import signals
from redis.asyncio import Redis
from redis.asyncio.client import Redis as RedisClient

from conf.celery_worker import IN_CELERY_WORKER_PROCESS
from conf.redis import RedisSettings



def _get_redis() -> RedisClient:
    _redis = Redis.from_url(
        RedisSettings.uri,
        decode_responses=True,
    )
    return _redis

class RedisClientWrapper:

    def __init__(self, redis: RedisClient):
        self.redis = redis

    def __getattr__(self, item):
        exc = None
        for _ in range(3):
            try:
                return getattr(self.redis, item)
            except RuntimeError as e:
                self.redis = get_redis()
                exc = e

        raise exc


_redis_client: RedisClient | None = None

if not IN_CELERY_WORKER_PROCESS:
    _redis_client = _get_redis()

else:
    @signals.worker_process_init.connect
    def init_redis(*_, **__):
        global _redis_client
        _redis_client = _get_redis()

    @signals.worker_init.connect
    def init_redis_fallback(*_, **__):
        global _redis_client
        _redis_client = _get_redis()


def get_redis() -> RedisClient:
    global _redis_client
    if not _redis_client or IN_CELERY_WORKER_PROCESS:
        _redis_client = _get_redis()

    return _redis_client