from components.parsing.models import DemoParsingState
from src.db.models.base import BaseMongoModel


class Player(BaseMongoModel):

    steam_id: str
    display_name: str
    rank: int | None = None
    profile_url: str | None = None
    avatar_url: str | None = None
    steam_profile_name: str | None = None


class Match(BaseMongoModel):

    cs2_match_id: int
    map_name: str
    match_code: str
    player_steam_ids: list[str]
    t_score: int
    ct_score: int

    demo_url: str | None = None


class PlayerMatchStat(BaseMongoModel):
    player_steam_id: str
    cs2_match_id: int
    kills: int
    deaths: int
    assists: int


class PlayerRankChange(BaseMongoModel):
    player_steam_id: str
    cs2_match_id: int
    old_rank: int | None = None
    new_rank: int


class MatchStatsWebhook(BaseMongoModel):
    url: str
    active: bool
    expected_steam_ids: list[str]

class MatchSource(BaseMongoModel):
    steam_id: str
    auth_code: str
    last_match_code: str
    active: bool


# Temporary not needed
class DemoParsingTask(BaseMongoModel):
    match_code: str
    task_id: str
    success: bool
    state: DemoParsingState
    error_message: str | None = None