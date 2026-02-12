import logging
from typing import Any

import aiohttp

from components.steam_connector.models import CS2DemoInfo
from conf.steam_connector import STEAM_CONNECTOR_HOST, STEAM_CONNECTOR_PORT, STEAM_CONNECTOR_TIMEOUT


class SteamClientConnectionError(Exception):
    pass


logger = logging.getLogger(__name__)


class SteamConnectorClient:
    base_url = f"http://{STEAM_CONNECTOR_HOST}:{STEAM_CONNECTOR_PORT}"

    def __init__(
        self,
    ) -> None:
        self._timeout = aiohttp.ClientTimeout(total=STEAM_CONNECTOR_TIMEOUT)
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()


    async def __aenter__(self) -> "SteamConnectorClient":
        return self

    async def __aexit__(self, *_, **__) -> None:
        await self.close()


    async def get_demo_url(self, match_code: str) -> CS2DemoInfo:
        response: dict = await self._safe_request(
            method="GET",
            url="/api/cs2/demo/",
            query_params={"match_code": match_code},
        )
        return CS2DemoInfo.model_validate(response)


    async def is_connector_logged_in(self):
        response: dict = await self._safe_request(
            method="GET",
            url="/api/steam/login_info/",
        )

        return response.get("username") is not None

    async def _safe_request(
        self,
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
        query_params: dict[str, Any] | None = None,
    ) -> Any:

        logger.info("SteamConnectorClient[_safe_request]: Requesting url: %s:%s", method, url)

        full_url = f"{self.base_url}{url}"

        session = await self._get_session()

        try:
            async with session.request(
                method=method.upper(),
                url=full_url,
                json=payload,
                params=query_params,
            ) as resp:

                if resp.status >= 400:
                    text = await resp.text()
                    raise SteamClientConnectionError(
                        f"Steam connector error {resp.status}: {text}"
                    )

                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await resp.json()

                return await resp.text()

        except aiohttp.ClientError as e:
            logger.exception("SteamConnectorClient[_safe_request]:", exc_info=e)
            raise SteamClientConnectionError(
                f"Steam connector request failed: {e}"
            ) from e