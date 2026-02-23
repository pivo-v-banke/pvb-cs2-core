import asyncio
import logging
from abc import abstractmethod, ABC

import aiohttp
from anyio.functools import lru_cache

from components.ranking.models import RANK_DESCRIPTIONS
from components.webhook.models import WebhookSendResult, WebhookSendStatus, MatchStatWebhookBody, WebhookType, \
    PlayerStatWebhookBody, WebhookBaseBody, CalibrationWebhookBody
from db import get_database
from db.managers.managers import MatchManager, WebhookManager, PlayerRankChangeManager, \
    PlayerMatchStatManager, PlayerManager
from db.models.models import Match, Webhook, Player, PlayerMatchStat, PlayerRankChange

logger = logging.getLogger(__name__)


class BaseWebhookSender(ABC):


    def __init__(self):
        self.db = get_database()
        self.match_manager = MatchManager(self.db)
        self.webhook_manager = WebhookManager(self.db)
        self.rank_change_manager = PlayerRankChangeManager(self.db)
        self.stats_manager = PlayerMatchStatManager(self.db)
        self.player_manager = PlayerManager(self.db)

    async def send_all(self) -> dict[str, WebhookSendResult]:
        webhooks = await self.webhook_manager.list_(
            filter_by={
                "active": True,
            }
        )
        tasks = []
        for webhook in webhooks:
            tasks.append(
                self.send(webhook)
            )

        results = await asyncio.gather(*tasks)
        return {
            result.id: result for result in results
        }

    async def send(self, webhook: str | Webhook) -> WebhookSendResult:

        if not isinstance(webhook, Webhook):
            webhook: Webhook = await self._get_webhook(webhook)


        if not webhook.url:
            return WebhookSendResult(id=webhook.id, status=WebhookSendStatus.NO_URL)

        if not webhook.active:
            return WebhookSendResult(id=webhook.id, status=WebhookSendStatus.DISABLED)


        webhook_body: WebhookBaseBody = await self._get_body(webhook.id)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook.url, json=webhook_body.model_dump(mode="json")) as response:
                    response.raise_for_status()
                    logger.info("MatchStatWebhookSenderMatchStatWebhookSender: Webhook %s sent successfully",
                                webhook.url)
                    return WebhookSendResult(id=webhook.id, status=WebhookSendStatus.SUCCESS)

        except Exception as exc:
            logger.exception(exc)
            return WebhookSendResult(id=webhook.id, status=WebhookSendStatus.FAILED)

        finally:
            await session.close()


    @lru_cache
    async def _get_webhook(self, webhook_id: str) -> Webhook:
        webhook = await self.webhook_manager.get(id_=webhook_id, raise_not_found=True)

        return webhook

    @abstractmethod
    async def _get_body(self, webhook_id: str) -> WebhookBaseBody:
        pass


class MatchStatWebhookSender(BaseWebhookSender):

    def __init__(self, match_code: str):
        super().__init__()
        self.match_code = match_code

    async def send(self, webhook: str | Webhook) -> WebhookSendResult:
        if not isinstance(webhook, Webhook):
            webhook: Webhook = await self._get_webhook(webhook)

        match: Match = await self._get_match()

        logger.info("MatchStatWebhookSender: Checking webhook %s for match %s", webhook.url,
                    self.match_code)

        expected_steam_ids = set(webhook.expected_steam_ids)
        actual_steam_ids = set(match.player_steam_ids)

        if not expected_steam_ids.intersection(actual_steam_ids):
            return WebhookSendResult(id=webhook.id, status=WebhookSendStatus.NO_INTERESTS)

        return await super().send(webhook)


    @lru_cache
    async def _get_match(self) -> Match:
        match = await self.match_manager.get(raise_not_found=True, match_code=self.match_code)

        return match


    async def _get_body(self, webhook_id: str) -> MatchStatWebhookBody:
        match: Match = await self._get_match()
        players: list[Player] =  await self.player_manager.list_(
            filter_by={
                "steam_id": {
                    "$in": match.player_steam_ids
                }
            }
        )
        match_stats: list[PlayerMatchStat] = await self.stats_manager.list_(
            filter_by={
                "cs2_match_id": match.cs2_match_id,
                "player_steam_id": {
                    "$in": match.player_steam_ids
                }
            }
        )
        rank_changes: list[PlayerRankChange] = await self.rank_change_manager.list_(
            filter_by={
                "cs2_match_id": match.cs2_match_id,
                "player_steam_id": {
                    "$in": match.player_steam_ids
                }
            }
        )
        return MatchStatWebhookBody(
            webhook_type=WebhookType.MATCH_STATS,
            webhook_id=webhook_id,
            match=match,
            stats=match_stats,
            rank_changes=rank_changes,
            players=players,
            rank_descriptions=RANK_DESCRIPTIONS,
        )


class PlayerStatWebhookSender(BaseWebhookSender):

    def __init__(self, player_steam_ids: list[str]):
        super().__init__()
        self.player_steam_ids = player_steam_ids


    async def _get_body(self, webhook_id: str) -> PlayerStatWebhookBody:

        players: list[Player] = await self.player_manager.list_(
            filter_by={
                "steam_id": {
                    "$in": self.player_steam_ids
                }
            }
        )

        return PlayerStatWebhookBody(
            webhook_type=WebhookType.PLAYER_STATS,
            webhook_id=webhook_id,
            players=players,
            rank_descriptions=RANK_DESCRIPTIONS,
        )



class CalibrationWebhookSender(BaseWebhookSender):


    async def _get_body(self, webhook_id: str) -> CalibrationWebhookBody:

        webhook = await self._get_webhook(webhook_id)

        players: list[Player] = await self.player_manager.list_(
            filter_by={
                "steam_id": {
                    "$in": webhook.expected_steam_ids
                }
            }
        )

        return CalibrationWebhookBody(
            webhook_type=WebhookType.CALIBRATION,
            webhook_id=webhook_id,
            players=players,
            rank_descriptions=RANK_DESCRIPTIONS,
        )
