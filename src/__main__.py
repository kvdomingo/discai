import asyncio
import re
from collections.abc import Callable
from textwrap import dedent
from time import time
from typing import cast

from dependency_injector.wiring import Provide, inject
from discord import Intents, Message, Thread
from discord.ext.commands import Bot, Cog
from langchain.messages import AIMessage, HumanMessage, SystemMessage
from loguru import logger

from src.dependencies import Container
from src.models.chat import get_chat_model, get_title_model
from src.repositories.discord import DiscordRepository
from src.repositories.generated.messages import CreateMessagesParams
from src.repositories.generated.models import ChatRole
from src.repositories.jev import JevRepository
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

    @inject
    @Cog.listener()
    async def on_message(
        self,
        message: Message,
        *,
        q: Querier = Provide[Container.querier],
        jev: JevRepository = Provide[Container.jev_repo],
        make_discord: Callable[..., DiscordRepository] = Provide[
            Container.discord_repo.provider
        ],
    ):
        # Interaction w/ DiscAI happens when
        # - User sends a regular message in a channel mentioning DiscAI
        # - User sends a message in a thread that was created from a previous message
        #   mentioning DiscAI
        d = make_discord(client=self.client, message=message)

        if d.is_author_bot:
            return

        if not ((d.message.thread is None and d.is_user_mentioned) or d.is_from_thread):
            return

        async with d.message.channel.typing():
            if d.is_from_thread:
                conversation = (
                    await q.conversations.get_conversation_by_guild_channel_id(
                        guild_id=d.message.guild.id,
                        channel_id=d.message.channel.id,
                    )
                )
                if conversation is None:
                    return

                thread = cast(Thread, d.message.channel)
            else:
                thread = await d.create_new_thread()
                conversation = await q.conversations.create_conversation(
                    guild_id=d.message.guild.id,
                    channel_id=thread.id,
                )
                if conversation is None:
                    raise RuntimeError("Failed to create conversation in DB")

                await q.db.commit()

            history = []
            async for h in q.messages.list_messages_in_conversation(id=conversation.id):
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
            prompt = HumanMessage(re.sub(r"\s*<@\d+>\s*", "", d.message.content))
            stream_t0 = time()
            full_message = ""
            new_message: Message | None = None
            history = [instructions, *history, prompt]
            try:
                async for chunk in llm.astream(history):
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
                                conversation_id=conversation.id,
                                author_id=d.message.author.id,
                                chat_role=ChatRole.USER,
                                content=prompt.text,
                            ),
                            CreateMessagesParams(
                                conversation_id=conversation.id,
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
            else:
                should_rename = await jev.should_rename(
                    current_title=thread.name,
                    history=[h.text for h in history],
                )
                if should_rename:
                    res = await llm.ainvoke(
                        [
                            SystemMessage(settings.TITLE_SYSTEM_PROMPT),
                            HumanMessage(prompt.text),
                        ]
                    )
                    await thread.edit(name=res.text)


async def main():
    container = Container()
    container.wire(modules=[__name__])

    await bot.add_cog(BotCog(bot))
    await bot.start(settings.DISCORD_TOKEN.get_secret_value())


if __name__ == "__main__":
    asyncio.run(main())
