import asyncio
import functools
import logging
from logging.config import dictConfig
from typing import Callable, Awaitable, TypeVar, Any, Coroutine, ParamSpec

from asgiref.sync import async_to_sync
from celery import Celery, signals

from conf.logging import LOGGING_CONFIG
from conf.redis import RedisSettings


dictConfig(LOGGING_CONFIG)

@signals.setup_logging.connect()
def _celery_setup_logging(*args, **kwargs):
    dictConfig(LOGGING_CONFIG)

@signals.worker_process_init.connect()
def _celery_worker_process_init(*args, **kwargs):

    dictConfig(LOGGING_CONFIG)


celery_app = Celery(
    "app",
    broker=RedisSettings.uri,
    backend=RedisSettings.uri,
)
celery_app.conf.include = ["tasks"]


T = TypeVar("T")
P = ParamSpec("P")

def async_context(func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, T]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:

        return async_to_sync(func)(*args, **kwargs)

    return wrapper