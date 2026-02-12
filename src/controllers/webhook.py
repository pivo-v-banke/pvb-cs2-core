from starlette.responses import Response

from api_models.webhook import MatchStatsWebhookPayload
from db import get_mongo_db
from db.managers.managers import MatchStatsWebhookManager
from db.models.models import MatchStatsWebhook


async def webhook_list_controller() -> list[MatchStatsWebhook]:
    manager = MatchStatsWebhookManager(get_mongo_db())

    return await manager.list_()

async def webhook_detail_controller(webhook_id: str) -> MatchStatsWebhook:
    manager = MatchStatsWebhookManager(get_mongo_db())

    return await manager.get(id_=webhook_id, raise_not_found=True)


async def webhook_create_controller(payload: MatchStatsWebhookPayload) -> MatchStatsWebhook:
    manager = MatchStatsWebhookManager(get_mongo_db())

    return await manager.create(payload.model_dump())

async def webhook_patch_controller(webhook_id: str, payload: MatchStatsWebhookPayload) -> MatchStatsWebhook:
    manager = MatchStatsWebhookManager(get_mongo_db())

    return await manager.update(id_=webhook_id, patch=payload.model_dump())


async def webhook_delete_controller(webhook_id: str) -> Response:
    manager = MatchStatsWebhookManager(get_mongo_db())

    await manager.delete(id_=webhook_id)

    return Response(status_code=204)