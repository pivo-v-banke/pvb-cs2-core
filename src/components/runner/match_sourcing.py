import asyncio
import logging

from components.steam_connector.steam_api import SteamAPIClient
from db import get_database
from db.managers.managers import MatchSourceManager, MatchManager
from db.models.models import MatchSource
from utils.concurrency import RedisLockException

logger = logging.getLogger(__name__)

class MatchSourceCollector:

    def __init__(self):
        self.db = get_database()
        self.source_manager = MatchSourceManager(self.db)
        self.match_manager = MatchManager(self.db)


    async def rollback_all_sources(self):
        pass

    async def collect_all_sources(self) -> None:
        logger.info(f'MatchSourceCollector: Collecting all sources')

        sources = await self.source_manager.list_(filter_by={"active": True})

        tasks = []

        async def _get_source_match_codes(source_: MatchSource) -> tuple[MatchSource, list[str]]:
            try:
                return source_, await self._get_source_match_codes(source_)
            except Exception as exc:
                logger.error("MatchSourceCollector: Failed to collect source %s: %s", source_, exc.args[0])
                return source_, []


        for source in sources:
            tasks.append(
                _get_source_match_codes(source)
            )

        results = await asyncio.gather(*tasks)
        update_last_code_tasks = []
        all_match_codes = []

        for source, match_codes in results:
            if not match_codes:
                continue

            update_last_code_tasks.append(
                self._update_last_code(source, match_codes)
            )
            all_match_codes.extend(match_codes)

        await asyncio.gather(*update_last_code_tasks)
        await self._run_parsing_for_codes(all_match_codes)


    async def collect_source(self, source: MatchSource | str) -> None:
        logger.info(f'MatchSourceCollector: Collecting from source: {source}')
        if not isinstance(source, MatchSource):
            source = await self.source_manager.get(id_=source, raise_not_found=True)

        if not source.active:
            logger.info(f'MatchSourceCollector: Source {source} not active, skipping')
            return

        match_codes = await self._get_source_match_codes(source)

        await asyncio.gather(
            self._run_parsing_for_codes(match_codes),
            self._update_last_code(source, match_codes),
        )

    @staticmethod
    async def _get_source_match_codes(source: MatchSource) -> list[str]:
        async with SteamAPIClient() as client:
            match_codes = await client.get_match_history(
                player_steam_id=source.steam_id,
                access_code=source.auth_code,
                known_match_code=source.last_match_code,
            )

        return match_codes


    async def _update_last_code(self, source: MatchSource, match_codes: list[str]) -> None:
        if not match_codes:
            return

        last_match_code = match_codes[-1]
        first_match_code = match_codes[0]
        await self.source_manager.update(
            id_=source.id,
            patch={
                "last_match_code": last_match_code,
                "first_match_code": first_match_code,
            }
        )

    async def _run_parsing_for_codes(self, match_codes: list[str]) -> None:
        from components.runner.parsing_runner import run_demo_parsing

        if not match_codes:
            return

        match_codes = set(match_codes)  # deduplication

        for match_code in match_codes:
            try:
                await run_demo_parsing(match_code)
            except RedisLockException:
                logger.warning(
                    "MatchSourceCollector: Parsing for match code %s already in progress, skipping",
                    match_code
                )
