from discord import Message, Thread
from discord.ext.commands import Bot

from src.settings import settings


class DiscordMessageRepository:
    def __init__(self, *, client: Bot, message: Message):
        self.client = client
        self.message = message

    @property
    def is_from_thread(self) -> bool:
        return isinstance(self.message.channel, Thread)

    @property
    def is_from_channel(self) -> bool:
        return not isinstance(self.message.channel, Thread)

    @property
    def is_author_bot(self) -> bool:
        return self.message.author.bot

    @property
    def is_user_mentioned(self) -> bool:
        return self.client.user in self.message.mentions

    async def create_new_thread(self) -> Thread:
        return await self.message.create_thread(
            name=settings.NEW_SESSION_TITLE_PLACEHOLDER
        )
