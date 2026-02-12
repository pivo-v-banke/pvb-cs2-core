import uuid
from datetime import datetime
from typing import Any

from bson import ObjectId
from pydantic import BaseModel, Field


class BaseMongoModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created: datetime | None = None
    updated: datetime | None = None