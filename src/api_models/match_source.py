from pydantic import BaseModel


class MatchSourcePayload(BaseModel):
    steam_id: str
    auth_code: str
    last_match_code: str
    active: bool