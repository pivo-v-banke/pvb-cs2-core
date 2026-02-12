import asyncio
import logging
import random
from typing import Any

import aiohttp

from conf.steam_connector import (
    STEAM_API_KEY,
    STEAM_API_MAX_PARALLEL_CONNECTIONS,
    STEAM_API_TIMEOUT,
)
from utils.concurrency import RedisSemaphore

logger = logging.getLogger(__name__)


class SteamAPIClientError(Exception):
    pass


class SteamAPIClient:
    base_url = "https://api.steampowered.com"
    max_ids_per_request = 100

    def __init__(self) -> None:
        self._api_key = STEAM_API_KEY
        self._timeout = aiohttp.ClientTimeout(total=STEAM_API_TIMEOUT)
        self._session: aiohttp.ClientSession | None = None
        self._semaphore = RedisSemaphore(
            "steam-api-client-semaphore",
            capacity=STEAM_API_MAX_PARALLEL_CONNECTIONS,
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> "SteamAPIClient":
        return self

    async def __aexit__(self, *_, **__) -> None:
        await self.close()

    async def get_profiles_info(self, steam_ids: list[str]) -> dict[str, dict[str, Any] | None]:
        result: dict[str, dict[str, Any] | None] = {sid: None for sid in steam_ids}

        if not self._api_key or not self._api_key.strip():
            logger.warning("SteamAPIClient: STEAM_API_KEY not provided; cannot fetch profiles")
            return result

        if not steam_ids:
            return result

        await self._semaphore.acquire()
        try:
            for i in range(0, len(steam_ids), self.max_ids_per_request):
                batch = steam_ids[i : i + self.max_ids_per_request]

                params = {
                    "key": self._api_key,
                    "steamids": ",".join(str(x) for x in batch),
                }


                data = await self._safe_request(
                    method="GET",
                    url="/ISteamUser/GetPlayerSummaries/v2/",
                    query_params=params,
                )
                players = (
                    data.get("response", {}).get("players", [])
                    if isinstance(data, dict)
                    else []
                )

                for p in players:
                    sid = p.get("steamid") if isinstance(p, dict) else None
                    if sid in result:
                        result[sid] = p

            return result
        finally:
            await self._semaphore.release()


    async def get_match_history(
        self,
        player_steam_id: str,
        access_code: str,
        known_match_code: str,
    ) -> list[str]:
        result: list[str] = []
        current_code = known_match_code

        await self._semaphore.acquire()
        try:
            while True:
                data = await self._safe_request(
                    method="GET",
                    url="/ICSGOPlayers_730/GetNextMatchSharingCode/v1/",
                    query_params={
                        "key": self._api_key,
                        "steamid": player_steam_id,
                        "steamidkey": access_code,
                        "knowncode": current_code,
                    },
                )

                next_code = (
                    data.get("result", {}).get("nextcode")
                    if isinstance(data, dict)
                    else None
                )

                if not next_code or next_code == "n/a":
                    break

                result.append(next_code)
                current_code = next_code

            return result
        finally:
            await self._semaphore.release()


    async def _safe_request(
        self,
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
        query_params: dict[str, Any] | None = None,
    ) -> Any:
        logger.debug("SteamAPIClient[_safe_request]: Requesting url: %s:%s", method, url)

        if not url.startswith("/"):
            url = f"/{url}"

        full_url = f"{self.base_url}{url}"
        session = await self._get_session()

        try:
            await asyncio.sleep(random.randint(200, 2000) / 1000)
            async with session.request(
                method=method.upper(),
                url=full_url,
                json=payload,
                params=query_params,
            ) as resp:
                if resp.status in (401, 403):
                    text = await resp.text()
                    raise SteamAPIClientError(f"Steam API key invalid (HTTP {resp.status}): {text}")

                if resp.status >= 400:
                    text = await resp.text()
                    raise SteamAPIClientError(f"Steam API error {resp.status}: {text}")

                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await resp.json(content_type=None)

                return await resp.text()

        except aiohttp.ClientError as e:
            logger.exception("SteamAPIClient[_safe_request]:", exc_info=e)
            raise SteamAPIClientError(f"Steam API request failed: {e}") from e
