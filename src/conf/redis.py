import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")
REDIS_LOCK_TTL = int(os.getenv("REDIS_LOCK_TTL", "900"))  # 15 minutes
REDIS_LOCK_TIMEOUT = int(os.getenv("REDIS_LOCK_TIMEOUT", "300")) # 5 minutes

class RedisSettings:
    host = REDIS_HOST
    port = REDIS_PORT
    db = REDIS_DB
    uri = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"