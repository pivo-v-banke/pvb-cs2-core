from pydantic import BaseModel


class MatchStatsWebhookPayload(BaseModel):
    url: str
    active: bool
    expected_steam_ids: list[str]