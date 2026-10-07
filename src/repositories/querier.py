from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.generated import conversations, messages


class Querier:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.conversations = conversations.AsyncQuerier(conn=db)
        self.messages = messages.AsyncQuerier(conn=db)
