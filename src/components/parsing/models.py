from pydantic import BaseModel

from utils.base_types import StringEnum


class DemoParsingState(StringEnum):
    NOT_PARSED = "NOT_PARSED"
    IN_PROGRESS = "IN_PROGRESS"
    ERROR = "ERROR"
    ALREADY_PARSED = "ALREADY_PARSED"
    SUCCESS = "SUCCESS"


class PlayerInfo(BaseModel):
    steam_id: str
    display_name: str | None = None


class MatchInfo(BaseModel):
    player_steam_ids: list[str]
    t_score: int
    ct_score: int
    map_name: str


class PlayerStatInfo(BaseModel):
    steam_id: str
    kills: int
    deaths: int
    assists: int
