from starlette.responses import Response

from api_models.webhook import MatchStatsWebhookPayload, PlayerStatWebhookRequestBody
from components.webhook.models import WebhookSendResult
from components.webhook.sender import PlayerStatWebhookSender
from db import get_mongo_db
from db.managers.managers import WebhookManager, MatchManager
from db.models.models import Webhook, Match
from tasks import DemoParsingContext, send_webhooks_task


async def webhook_list_controller() -> list[Webhook]:
    manager = WebhookManager(get_mongo_db())

    return await manager.list_()

async def webhook_detail_controller(webhook_id: str) -> Webhook:
    manager = WebhookManager(get_mongo_db())

    return await manager.get(id_=webhook_id, raise_not_found=True)


async def webhook_create_controller(payload: MatchStatsWebhookPayload) -> Webhook:
    manager = WebhookManager(get_mongo_db())

    return await manager.create(payload.model_dump())

async def webhook_patch_controller(webhook_id: str, payload: MatchStatsWebhookPayload) -> Webhook:
    manager = WebhookManager(get_mongo_db())

    return await manager.update(id_=webhook_id, patch=payload.model_dump())


async def webhook_delete_controller(webhook_id: str) -> Response:
    manager = WebhookManager(get_mongo_db())

    await manager.delete(id_=webhook_id)

    return Response(status_code=204)


async def send_match_stats_webhook_controller(match: str):
    filter_by = {}
    if str(match).startswith("CSGO"):
        filter_by["match_code"] = match
    elif match.isdigit():
        filter_by["cs2_match_id"] = int(match)
    else:
        raise ValueError("Invalid match identity")


    match: Match = await MatchManager(get_mongo_db()).get(**filter_by, raise_not_found=True)
    context = DemoParsingContext(
        match=match,
        match_code=match.match_code,
        lock_key=match.match_code,
    )
    send_webhooks_task.apply_async(args=(context.model_dump(),))


async def send_player_stats_webhook_controller(webhook_id: str, body: PlayerStatWebhookRequestBody) -> WebhookSendResult:
    sender = PlayerStatWebhookSender(player_steam_ids=body.player_steam_ids)
    webhook = await WebhookManager(get_mongo_db()).get(id_=webhook_id, raise_not_found=True)
    result = await sender.send(webhook=webhook)

    return result