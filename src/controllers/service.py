from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse


def ping_controller(request: Request) -> PlainTextResponse:

    return PlainTextResponse("pong")