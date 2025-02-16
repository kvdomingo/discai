from enum import StrEnum

from pydantic import Field, ConfigDict
from ulid import ULID

from .base import BaseModel


class ChatRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Conversation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    guild_id: int
    channel_id: int


class Message(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation_id: ULID
    chat_role: ChatRole
    content: str
    author_id: int | None = Field(None)
