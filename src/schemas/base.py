from datetime import datetime

from pydantic import BaseModel as PydanticBaseModel, Field
from ulid import ULID


class BaseModel(PydanticBaseModel):
    id: ULID | None = Field(None)
    created_at: datetime | None = Field(None)
