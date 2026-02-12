import logging

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

class APIKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, api_key: str, api_key_required: bool = True):
        super().__init__(app)
        self.api_key = api_key
        self.api_key_required = api_key_required

    async def dispatch(self, request: Request, call_next):
        if not self.api_key_required:
            return await call_next(request)

        if request.url.path in ("/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        client_key = request.headers.get("X-API-Key")

        if not client_key or client_key != self.api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized"},
            )

        response = await call_next(request)
        return response


class ExceptionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, exc_class: type[Exception], status_code: int = 500):
        super().__init__(app)
        self.exc_class = exc_class
        self.status_code = status_code

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)

        except self.exc_class as exc:
            logger.exception(exc)
            return JSONResponse(
                status_code=self.status_code,
                content={"detail": str(exc)},
            )
