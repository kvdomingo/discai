import asyncio
import re

from agno.run.response import RunResponse
from discord import Intents, Message, Thread
from discord.ext.commands import Bot, Cog
from loguru import logger
from sqlalchemy import text

from src.agent import get_chat_agent, title_agent
from src.db import get_db
from src.settings import settings

intents = Intents.default()
intents.message_content = True

bot = Bot(command_prefix="ai!", intents=intents)


class BotCog(Cog):
    def __init__(self, client: Bot):
        self.client = client

    @Cog.listener()
    async def on_ready(self):
        logger.info("Hello, Discord!")

    @Cog.listener()
    async def on_message(self, message: Message):
        # Interaction w/ DiscAI happens when
        # - User sends a regular message in a channel mentioning DiscAI
        # - User sends a message in a thread that was created from a previous message mentioning DiscAI

        if message.author.bot:
            return

        if not (
            (message.thread is None and self.client.user in message.mentions)
            or isinstance(message.channel, Thread)
        ):
            return

        async with message.channel.typing(), get_db() as db:
            is_new_thread = False

            if isinstance(message.channel, Thread):
                thread_in_db = (
                    (
                        await db.execute(
                            text("""
                            SELECT * FROM agent_sessions
                            WHERE session_id = :session_id
                            LIMIT 1
                            """),
                            {"session_id": str(message.channel.id)},
                        )
                    )
                    .mappings()
                    .first()
                )

                if thread_in_db is None:
                    return

                thread_id = thread_in_db["session_id"]
            else:
                new_thread = await message.create_thread(
                    name=settings.NEW_SESSION_TITLE_PLACEHOLDER
                )
                is_new_thread = True
                thread_id = new_thread.id

            agent = get_chat_agent(
                conversation_id=str(thread_id),
                user_id=str(message.author.id),
            )
            # Filter out Discord tags/mentions
            content = re.sub(r"\s*<@\d+>\s*", "", message.content)
            res: RunResponse = await agent.arun(content)

            if is_new_thread:
                thread = message.thread
            else:
                thread = message.channel

            await thread.send(res.content)

            if thread.name == settings.NEW_SESSION_TITLE_PLACEHOLDER:
                res = await title_agent.arun(content)
                await thread.edit(name=res.content)


async def main():
    await bot.add_cog(BotCog(bot))
    await bot.start(settings.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
