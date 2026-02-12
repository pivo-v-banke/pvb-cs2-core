from celery_app import celery_app, async_context
from components.runner.match_sourcing import MatchSourceCollector

__all__ = [
    "collect_demos"
]


@celery_app.task(queue="demo_collecting")
@async_context
async def collect_demos(match_source_id: str | None = None):
    collector = MatchSourceCollector()
    if match_source_id:
        await collector.collect_source(match_source_id)
    else:
        await collector.collect_all_sources()