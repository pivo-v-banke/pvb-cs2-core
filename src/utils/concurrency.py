import asyncio
import datetime
import logging
import uuid
from typing import Self

from conf.celery_worker import IN_CELERY_WORKER_PROCESS
from conf.redis import REDIS_LOCK_TIMEOUT, REDIS_LOCK_TTL
from redis_client import get_redis
from utils.time_utils import utcnow


class RedisLockException(Exception):
    pass

logger = logging.getLogger(__name__)

class RedisLock:

    def __init__(self, key: str, ttl: int | None = None, timeout: int | None = None, raise_locked: bool = False):
        self.key = key
        self.ttl = ttl if ttl is not None else REDIS_LOCK_TTL
        self.timeout = timeout if timeout is not None else REDIS_LOCK_TIMEOUT
        self.raise_locked = raise_locked
        self.redis_client = get_redis()


    async def acquire(self, raise_locked: bool | None = None) -> Self:
        is_locked = await self._is_locked()

        if raise_locked is None:
            raise_locked = self.raise_locked


        if raise_locked and is_locked:
            raise RedisLockException(f"Key {self.key} locked")

        now = utcnow()
        timeout_dt = now + datetime.timedelta(seconds=self.timeout)
        while is_locked:
            logger.debug(f"RedisLock: awaiting key {self.key}")
            is_locked = await self._is_locked()
            now = utcnow()
            if now > timeout_dt:
                raise RedisLockException(f"Key {self.key} locked. Timeout expired")

            await asyncio.sleep(1)

        await self.redis_client.set(self.key, 1)

    async def reacquire(self) -> Self:
        is_locked = await self._is_locked()
        if not is_locked:
            await self.acquire(raise_locked=False)

    async def release(self):
        if self._is_locked():
            await self.redis_client.delete(self.key)


    async def __aenter__(self) -> Self:
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()

    async def _is_locked(self) -> bool:
        return await self.redis_client.get(self.key) is not None



class RedisSemaphore:

    def __init__(
        self,
        key: str,
        capacity: int,
        ttl: int | None = None,
        timeout: int | None = None,
        raise_locked: bool = False,
    ):
        self.key = key
        self.capacity = capacity
        self.ttl = ttl if ttl is not None else REDIS_LOCK_TTL
        self.timeout = timeout if timeout is not None else REDIS_LOCK_TIMEOUT
        self.raise_locked = raise_locked
        self.redis = get_redis()

        self.token = uuid.uuid4().hex

    async def acquire(self, raise_locked: bool | None = None) -> Self:
        if raise_locked is None:
            raise_locked = self.raise_locked

        now = utcnow()
        timeout_dt = now + datetime.timedelta(seconds=self.timeout)

        while True:
            acquired = await self._try_acquire_once()

            if acquired:
                return self

            if raise_locked:
                raise RedisLockException(f"Semaphore {self.key} full")

            now = utcnow()
            if now > timeout_dt:
                raise RedisLockException(f"Semaphore {self.key} full. Timeout expired")

            logger.debug(f"RedisSemaphore: awaiting slot for {self.key}")
            await asyncio.sleep(1)

    async def reacquire(self) -> Self:
        present = await self._is_held_by_me()
        if not present:
            await self.acquire(raise_locked=False)
        return self

    async def refresh(self) -> None:
        now_ts = int(utcnow().timestamp())
        expires_at = now_ts + int(self.ttl)
        await self.redis.zadd(self.key, {self.token: expires_at}, xx=True)


        await self.redis.expire(self.key, int(self.ttl) * 2)

    async def release(self) -> None:
        await self.redis.zrem(self.key, self.token)

    async def __aenter__(self) -> Self:
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()

    async def _try_acquire_once(self) -> bool:
        now_ts = int(utcnow().timestamp())
        expires_at = now_ts + int(self.ttl)

        # Meow :3
        lua = """
        local key = KEYS[1]
        local token = ARGV[1]
        local now = tonumber(ARGV[2])
        local expires_at = tonumber(ARGV[3])
        local capacity = tonumber(ARGV[4])
        local key_ttl = tonumber(ARGV[5])

        -- remove expired tokens
        redis.call('ZREMRANGEBYSCORE', key, '-inf', now)

        local count = redis.call('ZCARD', key)
        if count < capacity then
            redis.call('ZADD', key, expires_at, token)
            redis.call('EXPIRE', key, key_ttl)
            return 1
        end
        return 0
        """

        key_ttl = max(int(self.ttl) * 2, 5)

        res = await self.redis.eval(
            lua,
            1,
            self.key,
            self.token,
            now_ts,
            expires_at,
            int(self.capacity),
            key_ttl,
        )
        return bool(res)

    async def _is_held_by_me(self) -> bool:
        score = await self.redis.zscore(self.key, self.token)
        if score is None:
            return False
        now_ts = int(utcnow().timestamp())
        return float(score) > now_ts