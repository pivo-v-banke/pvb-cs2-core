from pydantic import BaseModel

from components.ranking.models import RankDescription
from db.models.models import Match, PlayerMatchStat, PlayerRankChange, Player
from utils.base_types import StringEnum


class WebhookSendStatus(StringEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DISABLED = "DISABLED"
    NO_URL = "NO_URL"
    NO_INTERESTS = "NO_INTERESTS"


class WebhookBody(BaseModel):
    webhook_id: str
    match: Match
    stats: list[PlayerMatchStat]
    rank_changes: list[PlayerRankChange]
    players: list[Player]
    rank_descriptions: list[RankDescription]

class WebhookSendResult(BaseModel):
    id: str
    status: WebhookSendStatus
    message: str | None = None

    def __bool__(self) -> bool:
        return self.status == WebhookSendStatus.SUCCESS