from starlette.responses import Response

from api_models.match_source import MatchSourcePayload
from components.runner.match_sourcing import MatchSourceCollector
from db import get_mongo_db
from db.managers.managers import MatchSourceManager
from db.models.models import MatchSource
from tasks.collecting import collect_demos


async def collect_match_source_controller(match_source_id: str) -> None:

    collect_demos.apply_async(kwargs={'match_source_id': match_source_id})


async def collect_all_match_sources_controller() -> None:
    collect_demos.apply_async()

async def match_source_list_controller() -> list[MatchSource]:
    manager = MatchSourceManager(get_mongo_db())

    return await manager.list_()

async def match_source_detail_controller(match_source_id: str) -> MatchSource:
    manager = MatchSourceManager(get_mongo_db())

    return await manager.get(id_=match_source_id, raise_not_found=True)


async def match_source_create_controller(payload: MatchSourcePayload) -> MatchSource:
    manager = MatchSourceManager(get_mongo_db())

    return await manager.create(payload.model_dump())

async def match_source_patch_controller(match_source_id: str, payload: MatchSourcePayload) -> MatchSource:
    manager = MatchSourceManager(get_mongo_db())

    return await manager.update(id_=match_source_id, patch=payload.model_dump())


async def match_source_delete_controller(match_source_id: str) -> Response:
    manager = MatchSourceManager(get_mongo_db())

    await manager.delete(id_=match_source_id)

    return Response(status_code=204)