import bz2
import functools
import logging
import os
from pathlib import Path
from typing import Callable, Coroutine
from urllib.parse import urlparse, unquote

import aiohttp
from celery import Task
from pydantic import BaseModel

from celery_app import celery_app, async_context
from components.demo.processing import DemoProcessing
from components.parsing.checkers import DemoParsingDeduplicationChecker
from components.ranking.rank_updater import RankUpdater
from components.steam_connector.client import SteamConnectorClient
from components.steam_connector.models import CS2DemoInfo
from components.steam_connector.steam_api import SteamAPIClient
from components.webhook.sender import WebhookSender
from conf.demo import DEMO_BASE_DIR
from conf.parsing import PARSING_DEDUP_KEY_TTL
from db import get_database
from db.managers.managers import PlayerManager
from db.models.models import Match
from utils.concurrency import RedisLock


__all__ = [
    "DemoParsingContext",
    "request_demo_url_task",
    "download_demo_file_task",
    "parse_demo_task"
]

logger = logging.getLogger(__name__)

class DemoParsingContext(BaseModel):
    match_code: str
    lock_key: str
    demo_info: CS2DemoInfo | None = None
    demo_file_path: str | None = None
    match: Match | None = None
    match_was_created: bool | None = None


class DemoParsingError(Exception):
    pass

def unlock_on_error(func: Callable[[dict], Coroutine]) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            logger.exception(exc)
            context = kwargs.get("context", {})
            lock_key = context.get("lock_key", None)

            if not lock_key:
                for arg in args:
                    if isinstance(arg, dict):
                        lock_key = arg.get("lock_key", None)
                        if lock_key:
                            break
            if lock_key:
                lock = RedisLock(lock_key)
                await lock.release()

            else:
                logger.error("DemoParsing: Could not find lock key in call args")

            logger.exception(exc)
            raise exc


    return wrapper

@celery_app.task(queue="demo_parsing")
@async_context
@unlock_on_error
async def request_demo_url_task(context: dict) -> dict:
    context: DemoParsingContext = DemoParsingContext.model_validate(context)
    match_code = context.match_code

    await DemoParsingDeduplicationChecker.check_parsing_duplicate(match_code)
    parsing_lock = RedisLock(context.lock_key, ttl=PARSING_DEDUP_KEY_TTL)
    await parsing_lock.reacquire()

    async with SteamConnectorClient() as client:
        demo_info = await client.get_demo_url(match_code)

    context.demo_info = demo_info
    logger.info("request_demo_url_task: found demo url %s", demo_info.demo_url)
    return context.model_dump()


class DownloadDemoFileTask(Task):
    name = "download_demo_file"
    queue = "demo_parsing"

    retry_kwargs = {"max_retries": 5}

    @async_context
    @unlock_on_error
    async def run(self, context: dict) -> dict:
        context: DemoParsingContext = DemoParsingContext.model_validate(context)
        demo_info: CS2DemoInfo = context.demo_info
        match_code = demo_info.match_code
        demo_base_dir = Path(DEMO_BASE_DIR)
        demo_base_dir.mkdir(parents=True, exist_ok=True)

        demo_url = demo_info.demo_url
        if not demo_url:
            raise DemoParsingError(f"No demo url for {match_code}")

        url_name = self._filename_from_url(demo_url, match_code)
        if not url_name or url_name == "demo":
            url_name = f"{match_code}.dem"

        tmp_path = demo_base_dir / f"{match_code}__{url_name}.download"
        final_path = demo_base_dir / f"{match_code}__{url_name}"

        logger.info("DownloadDemoFileTask: Starting download demo file for %s. Output path: %s", match_code, final_path)
        async with aiohttp.ClientSession() as session:
            async with session.get(demo_url) as resp:
                resp.raise_for_status()

                with tmp_path.open("wb") as f:
                    async for chunk in resp.content.iter_chunked(1024 * 1024):
                        logger.info("DownloadDemoFileTask: Downloading %s...",match_code)
                        if chunk:
                            f.write(chunk)

        with tmp_path.open("rb") as f:
            head = f.read(16)

        is_bz2 = final_path.suffix.lower() == ".bz2" or self._looks_like_bz2_magic(head)

        if is_bz2:
            if final_path.suffix.lower() == ".bz2":
                out_path = final_path.with_suffix("")
            else:
                out_path = demo_base_dir / f"{match_code}__{Path(url_name).stem or match_code}.dem"

            with tmp_path.open("rb") as src, out_path.open("wb") as dst:
                dst.write(bz2.decompress(src.read()))

            tmp_path.unlink(missing_ok=True)
            result_path = out_path

        else:
            os.replace(tmp_path, final_path)
            result_path = final_path

        context.demo_file_path = str(result_path)
        return context.model_dump()

    @staticmethod
    def _filename_from_url(url: str, match_code: str) -> str:
        p = urlparse(url)
        name = Path(unquote(p.path)).name
        return name or match_code.replace("-", "_")

    @staticmethod
    def _looks_like_bz2_magic(first_bytes: bytes) -> bool:
        return len(first_bytes) >= 3 and first_bytes[:3] == b"BZh"


@celery_app.task(queue="demo_parsing")
@async_context
@unlock_on_error
async def parse_demo_task(context: dict) -> dict:
    context: DemoParsingContext = DemoParsingContext.model_validate(context)
    demo_file_path = context.demo_file_path

    demo_processing = DemoProcessing(demo_file_path, context.demo_info)
    match, created = await demo_processing.process_demo()
    context.match = match
    context.match_was_created = created

    return context.model_dump()


@celery_app.task(queue="demo_parsing")
@async_context
@unlock_on_error
async def rank_calculation_task(context: dict) -> dict:
    context: DemoParsingContext = DemoParsingContext.model_validate(context)
    cs2_match_id = context.match.cs2_match_id
    rank_updater = RankUpdater(cs2_match_id)
    await rank_updater.update_player_ranks()

    return context.model_dump()


class RefreshSteamProfilesTask(Task):
    name = "refresh_steam_profiles_task"
    queue = "demo_parsing"


    @async_context
    @unlock_on_error
    async def run(self, context: dict) -> dict:
        context: DemoParsingContext = DemoParsingContext.model_validate(context)
        player_steam_ids = context.match.player_steam_ids
        steam_api = SteamAPIClient()
        steam_profiles_info = await steam_api.get_profiles_info(player_steam_ids)
        player_manager = PlayerManager(get_database())

        logger.info("RefreshSteamProfilesTask: Updating steam profiles info for steam ids %s",  player_steam_ids)
        for steam_id, info in steam_profiles_info.items():
            if not info:
                logger.warning("RefreshSteamProfilesTask: No info for steam id %s", steam_id)
                continue

            profile_url = info.get("profileurl")
            avatar_url = info.get("avatarfull")
            steam_profile_name = info.get("personaname")
            data_to_update = {}
            if profile_url:
                data_to_update["profile_url"] = profile_url
            if avatar_url:
                data_to_update["avatar_url"] = avatar_url
            if steam_profile_name:
                data_to_update["steam_profile_name"] = steam_profile_name

            if data_to_update:
                await player_manager.update(
                    search_by={
                        "steam_id": steam_id,
                    },
                    patch=data_to_update
                )

        return context.model_dump()


@celery_app.task(queue="demo_parsing")
@async_context
@unlock_on_error
async def send_webhooks_task(context: dict) -> dict:
    context: DemoParsingContext = DemoParsingContext.model_validate(context)
    match_code = context.match.match_code
    sender = WebhookSender(match_code)
    await sender.send_all()

    return context.model_dump()


download_demo_file_task = celery_app.register_task(DownloadDemoFileTask)
refresh_steam_profiles_task = celery_app.register_task(RefreshSteamProfilesTask)