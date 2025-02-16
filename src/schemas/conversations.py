from enum import StrEnum

from pydantic import Field
from ulid import ULID

from .base import BaseModel


class ChatRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Conversation(BaseModel):
    guild_id: int
    channel_id: int


class Message(BaseModel):
    conversation_id: ULID
    chat_role: ChatRole
    content: str
    author_id: int | None = Field(None)
