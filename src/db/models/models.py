from components.parsing.models import DemoParsingState
from components.steam_connector.models import CS2DemoInfo
from db.models.base import BaseMongoModel


class Player(BaseMongoModel):

    steam_id: str
    display_name: str
    profile_url: str | None = None
    avatar_url: str | None = None
    steam_profile_name: str | None = None

    # stats
    rank: int | None = None
    avg_kd: float | None = None
    games_played: int | None = None
    plus_kd_games: int | None = None
    minus_kd_games: int | None = None



class Match(BaseMongoModel):

    cs2_match_id: int
    map_name: str
    match_code: str
    player_steam_ids: list[str]
    t_score: int
    ct_score: int

    demo_info: CS2DemoInfo | None = None


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


class Webhook(BaseMongoModel):
    url: str
    active: bool
    expected_steam_ids: list[str]

class MatchSource(BaseMongoModel):
    steam_id: str
    auth_code: str
    last_match_code: str
    first_match_code: str | None = None
    active: bool


# Temporary not needed
class DemoParsingTask(BaseMongoModel):
    match_code: str
    task_id: str
    success: bool
    state: DemoParsingState
    error_message: str | None = None