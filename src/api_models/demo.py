from pydantic import BaseModel


class RunDemoParsingRequest(BaseModel):
    match_code: str