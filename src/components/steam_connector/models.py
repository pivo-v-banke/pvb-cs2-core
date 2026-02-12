from pydantic import BaseModel


class SteamLoginInfo(BaseModel):
    username: str | None


class CS2DemoInfo(BaseModel):
    match_code: str
    match_id: int
    outcome_id: int
    token: int
    demo_url: str | None = None