import asyncio

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam
from discord import Intents, Message
from discord.ext.commands import Bot, Cog
from loguru import logger
from sqlalchemy import text

from src.db import get_db
from src.schemas.conversations import Conversation
from src.settings import settings

intents = Intents.default()
intents.message_content = True

ant = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

bot = Bot(command_prefix="ai!", intents=intents)


class BotCog(Cog):
    def __init__(self, client: Bot):
        self.client = client

    @Cog.listener()
    async def on_ready(self):
        logger.info("Hello, Discord!")

    @Cog.listener()
    async def on_message(self, message: Message):
        if self.client.user in message.mentions:
            async with message.channel.typing(), get_db() as db:
                # Select existing conversation
                res = (
                    (
                        await db.execute(
                            text("""
                            SELECT * FROM conversations
                            WHERE guild_id = :guild_id AND channel_id = :channel_id;
                            """),
                            {
                                "guild_id": message.guild.id,
                                "channel_id": message.channel.id,
                            },
                        )
                    )
                    .mappings()
                    .first()
                )

                if res is None:
                    # Create conversation if there is none yet in the current channel
                    res = await db.execute(
                        text("""
                        INSERT INTO conversations (guild_id, channel_id)
                        VALUES (:guild_id, :channel_id)
                        RETURNING *;
                        """),
                        {
                            "guild_id": message.guild.id,
                            "channel_id": message.channel.id,
                        },
                    )
                    await db.commit()

                    convo = Conversation.model_validate(res)

                    # Insert system prompt as the first message in the conversation
                    await db.execute(
                        text("""
                        INSERT INTO messages (conversation_id, chat_role, content, author_id)
                        VALUES (:conversation_id, 'system', :content, NULL);
                        """),
                        {
                            "conversation_id": str(convo.id),
                            "content": settings.BASE_PROMPT,
                        },
                    )
                else:
                    convo = Conversation.model_validate(res)

                content = message.content.replace(
                    f"<@{self.client.user.id}>", ""
                ).strip()

                # Insert user message
                await db.execute(
                    text("""
                    INSERT INTO messages (conversation_id, chat_role, content, author_id)
                    VALUES (:conversation_id, 'user', :content, :author_id);
                    """),
                    {
                        "conversation_id": str(convo.id),
                        "content": content,
                        "author_id": message.author.id,
                    },
                )

                res = await ant.messages.create(
                    max_tokens=1024,
                    messages=[MessageParam(role="user", content=content)],
                    model="claude-3-5-haiku-latest",
                    system=settings.BASE_PROMPT,
                )
                reply = "".join([c.text for c in res.content if c.type == "text"])

                # Insert LLM response
                await db.execute(
                    text("""
                    INSERT INTO messages (conversation_id, chat_role, content, author_id)
                    VALUES (:conversation_id, 'assistant', :content, NULL);
                    """),
                    {
                        "conversation_id": str(convo.id),
                        "content": reply,
                    },
                )

                await message.reply(reply)


async def main():
    await bot.add_cog(BotCog(bot))
    await bot.start(settings.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
