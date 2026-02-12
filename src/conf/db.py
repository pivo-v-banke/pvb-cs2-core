import os

MONGODB_HOST = os.getenv("MONGODB_HOST", "localhost")
MONGODB_PORT = int(os.getenv("MONGODB_PORT", "27017"))
MONGODB_DB = os.getenv("MONGODB_DB", "pvb-cs2")
MONGODB_USER = os.getenv("MONGODB_USER", "admin")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD", "admin")
MONGODB_MIN_POOL_SIZE = int(os.getenv("MONGODB_MIN_POOL_SIZE", "1"))
MONGODB_MAX_POOL_SIZE = int(os.getenv("MONGODB_MAX_POOL_SIZE", "10"))


class MongoSettings:

    host: str = MONGODB_HOST
    port: int = MONGODB_PORT
    db: str = MONGODB_DB
    min_pool_size: int = MONGODB_MIN_POOL_SIZE
    max_pool_size: int = MONGODB_MAX_POOL_SIZE
    username: str = MONGODB_USER
    password: str = MONGODB_PASSWORD

    uri: str = f"mongodb://{username}:{password}@{host}:{port}"