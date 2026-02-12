from celery import signals
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from conf.celery_worker import IN_CELERY_WORKER_PROCESS
from conf.db import MongoSettings


def get_mongo_client() -> AsyncIOMotorClient:
    _client = AsyncIOMotorClient(
        MongoSettings.uri,
        minPoolSize=MongoSettings.min_pool_size,
        maxPoolSize=MongoSettings.max_pool_size,
    )
    return _client


def get_database() -> AsyncIOMotorDatabase:
    return get_mongo_client()[MongoSettings.db]


_mongo_db: AsyncIOMotorDatabase | None = None


if not IN_CELERY_WORKER_PROCESS:
    _mongo_db = get_database()

else:
    @signals.worker_process_init.connect
    def init_db(*_, **__):
        global _mongo_db
        _mongo_db = get_database()


    @signals.worker_init.connect
    def init_db_fallback(*_, **__):
        global _mongo_db
        _mongo_db = get_database()

def get_mongo_db() -> AsyncIOMotorDatabase:
    global _mongo_db
    if _mongo_db is None or IN_CELERY_WORKER_PROCESS:
        _mongo_db = get_database()

    return _mongo_db