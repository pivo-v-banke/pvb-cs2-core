import logging

import celery

from components.steam_connector.client import SteamConnectorClient
from conf.parsing import PARSING_DEDUP_KEY_TTL
from tasks.demo import DemoParsingContext, request_demo_url_task, download_demo_file_task, parse_demo_task, \
    rank_calculation_task, refresh_steam_profiles_task, send_webhooks_task
from utils.concurrency import RedisLock


logger = logging.getLogger(__name__)

async def run_demo_parsing(match_code: str):

    logged_in = await SteamConnectorClient().is_connector_logged_in()
    if not logged_in:
        logger.error("run_demo_parsing: steam connector not logged in. Aborting")
        return

    context: DemoParsingContext = DemoParsingContext(
        match_code=match_code,
        lock_key=match_code
    )
    parsing_lock = RedisLock(context.lock_key, ttl=PARSING_DEDUP_KEY_TTL)
    await parsing_lock.acquire(raise_locked=True)

    try:
        chain = [
            request_demo_url_task.s(context.model_dump()),
            download_demo_file_task.s(),
            parse_demo_task.s(),
            rank_calculation_task.s(),
            refresh_steam_profiles_task.s(),
            send_webhooks_task.s(),
        ]

        workflow = celery.chain(*chain)
        workflow.apply_async()
        logger.info("run_demo_parsing: Run for match code %s", match_code)

    except Exception as exc:
        logger.exception("run_demo_parsing: Failed with error", exc_info=exc)
        await parsing_lock.release()

