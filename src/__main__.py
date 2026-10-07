import asyncio
import re
from textwrap import dedent
from time import time

from discord import Intents, Message, Thread
from discord.ext.commands import Bot, Cog
from langchain.messages import AIMessage, HumanMessage, SystemMessage
from loguru import logger

from src.db import get_db
from src.models import get_chat_model, get_title_model
from src.repositories.generated.messages import CreateMessagesParams
from src.repositories.generated.models import ChatRole
from src.repositories.querier import Querier
from src.settings import settings
from src.utils import alist

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
        # - User sends a message in a thread that was created from a previous message
        #   mentioning DiscAI

        if message.author.bot:
            return

        if not (
            (message.thread is None and self.client.user in message.mentions)
            or isinstance(message.channel, Thread)
        ):
            return

        async with message.channel.typing(), get_db() as db:
            q = Querier(db)

            if isinstance(message.channel, Thread):
                thread_in_db = (
                    await q.conversations.get_conversation_by_guild_channel_id(
                        guild_id=message.guild.id,
                        channel_id=message.channel.id,
                    )
                )
                if thread_in_db is None:
                    return

                thread = message.channel
            else:
                thread = await message.create_thread(
                    name=settings.NEW_SESSION_TITLE_PLACEHOLDER
                )
                thread_in_db = await q.conversations.create_conversation(
                    guild_id=message.guild.id,
                    channel_id=thread.id,
                )
                if thread_in_db is None:
                    raise RuntimeError("Failed to create conversation in DB")

                await q.db.commit()

            history = []
            async for h in q.messages.list_messages_in_conversation(id=thread_in_db.id):
                if h.chat_role == ChatRole.USER:
                    history.append(HumanMessage(h.content))
                if h.chat_role == ChatRole.ASSISTANT:
                    history.append(AIMessage(h.content))

            llm = get_chat_model()
            instructions = SystemMessage(
                dedent(f"""
                {settings.SYSTEM_PROMPT}

                {settings.SYSTEM_PROMPT_ADDITIONAL_CONTEXT}
                """).strip()
            )

            # Filter out Discord tags/mentions
            prompt = HumanMessage(re.sub(r"\s*<@\d+>\s*", "", message.content))
            stream_t0 = time()
            full_message = ""
            new_message: Message | None = None
            try:
                async for chunk in llm.astream([instructions, *history, prompt]):
                    full_message += chunk.text
                    if not full_message:
                        continue

                    if new_message is None:
                        new_message = await thread.send(full_message)
                        stream_t0 = time()
                    elif time() - stream_t0 > 1:
                        await new_message.edit(content=full_message)
                        stream_t0 = time()

                await alist(
                    q.messages.create_messages(
                        arg=[
                            CreateMessagesParams(
                                conversation_id=thread_in_db.id,
                                author_id=message.author.id,
                                chat_role=ChatRole.USER,
                                content=prompt.text,
                            ),
                            CreateMessagesParams(
                                conversation_id=thread_in_db.id,
                                author_id=None,
                                chat_role=ChatRole.ASSISTANT,
                                content=full_message,
                            ),
                        ]
                    )
                )
                await q.db.commit()
            except Exception as e:
                await thread.send(
                    dedent("""```
                    [SYSTEM] An unknown error occurred. Please try again later.
                    ```""").strip()
                )
                logger.exception(e)
                raise

            if new_message is None:
                raise ValueError("New message not found")

            await new_message.edit(content=full_message)

            if thread.name == settings.NEW_SESSION_TITLE_PLACEHOLDER:
                llm = get_title_model()
                res = await llm.ainvoke(
                    [
                        SystemMessage(settings.TITLE_SYSTEM_PROMPT),
                        HumanMessage(prompt.text),
                    ]
                )
                await thread.edit(name=res.text)


async def main():
    await bot.add_cog(BotCog(bot))
    await bot.start(settings.DISCORD_TOKEN.get_secret_value())


if __name__ == "__main__":
    asyncio.run(main())
