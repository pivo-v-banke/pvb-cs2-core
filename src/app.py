from contextlib import asynccontextmanager
from logging.config import dictConfig

from fastapi import FastAPI

from conf.logging import LOGGING_CONFIG
from db.managers.base import NotFoundError
from middlewares import APIKeyMiddleware, ExceptionMiddleware
from routes import prepare_routes


def prepare_app() -> FastAPI:
    dictConfig(LOGGING_CONFIG)

    fastapi_app = FastAPI()

    fastapi_app.add_middleware(
        ExceptionMiddleware,
        exc_class=ValueError,
        status_code=400,
    )
    fastapi_app.add_middleware(
        ExceptionMiddleware,
        exc_class=NotFoundError,
        status_code=404,
    )

    prepare_routes(fastapi_app)
    return fastapi_app


app = prepare_app()