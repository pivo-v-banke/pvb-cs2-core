import asyncio
import aiohttp
import logging
from typing import Any

from conf.steam_connector import STEAM_API_KEY, STEAM_API_MAX_PARALLEL_CONNECTIONS, STEAM_API_TIMEOUT
from utils.concurrency import RedisSemaphore

logger = logging.getLogger(__name__)


class SteamAPIClient:
    BASE_URL = "https://api.steampowered.com"
    MAX_IDS_PER_REQUEST = 100

    def __init__(self):
        self.api_key = STEAM_API_KEY
        self.timeout = STEAM_API_TIMEOUT
        self.semaphore = RedisSemaphore(
            "steam-api-client-semaphore",
            capacity=STEAM_API_MAX_PARALLEL_CONNECTIONS,
        )

    async def get_profiles_info(self, steam_ids: list[str]) -> dict[str, dict[str, Any] | None]:

        await self.semaphore.acquire()
        try:
            return await self._get_profiles_info(steam_ids)
        finally:
            await self.semaphore.release()

    async def _get_profiles_info(
        self,
        steam_ids: list[str],
    ) -> dict[str, dict[str, Any] | None]:
        result: dict[str, dict[str, Any] | None] = {sid: None for sid in steam_ids}

        if not self.api_key or not self.api_key.strip():
            logger.warning("SteamAPIClient: STEAM_API_KEY not provided; cannot fetch profiles")
            return result

        if not steam_ids:
            return result

        timeout = aiohttp.ClientTimeout(total=self.timeout)

        async with aiohttp.ClientSession(timeout=timeout) as session:

            for i in range(0, len(steam_ids), self.MAX_IDS_PER_REQUEST):
                batch = steam_ids[i:i + self.MAX_IDS_PER_REQUEST]

                params = {
                    "key": self.api_key,
                    "steamids": ",".join(str(x) for x in batch),
                }

                logger.debug(
                    "SteamAPIClient: fetching profile info for %s steam ids",
                    len(batch),
                )

                try:
                    async with session.get(
                        f"{self.BASE_URL}/ISteamUser/GetPlayerSummaries/v2/",
                        params=params,
                    ) as resp:

                        if resp.status in (401, 403):
                            logger.warning("SteamAPIClient: invalid Steam API key (HTTP %s)", resp.status)
                            return result

                        if resp.status != 200:
                            logger.warning(
                                "SteamAPIClient: request failed (HTTP %s)",
                                resp.status,
                            )
                            continue

                        data = await resp.json(content_type=None)

                except asyncio.TimeoutError:
                    logger.warning("SteamAPIClient: timeout fetching Steam profiles")
                    continue
                except aiohttp.ClientError as e:
                    logger.warning("SteamAPIClient: HTTP error fetching Steam profiles: %s", e)
                    continue
                except Exception as e:
                    logger.warning("SteamAPIClient: unexpected error fetching Steam profiles: %s", e)
                    continue

                players = (
                    data.get("response", {}).get("players", [])
                    if isinstance(data, dict)
                    else []
                )

                for p in players:
                    sid = p.get("steamid")
                    if sid in result:
                        result[sid] = p

        return result