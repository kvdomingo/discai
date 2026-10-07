import asyncio
import logging
from collections.abc import Callable
from time import time
from typing import cast

from dependency_injector.wiring import Provide, inject
from discord import Intents, Message, Thread
from discord.ext.commands import Bot, Cog
from langchain.messages import AIMessage, HumanMessage, SystemMessage
from loguru import logger

from src.application.logging import InterceptHandler
from src.application.messaging import render, strip_mentions
from src.dependencies import Container
from src.models.chat import get_chat_model, get_title_model
from src.repositories.discord import DiscordMessageRepository
from src.repositories.generated.messages import CreateMessagesParams
from src.repositories.generated.models import ChatRole
from src.repositories.queriers import AsyncQueriers
from src.repositories.typesafe import TypeSafeRepository
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
        logger.info("Hello, DiscAI!")

    @inject
    @Cog.listener()
    async def on_message(
        self,
        message: Message,
        *,
        q: AsyncQueriers = Provide[Container.queriers],
        jev: TypeSafeRepository = Provide[Container.typesafe_repo],
        make_discord: Callable[..., DiscordMessageRepository] = Provide[
            Container.discord_message_repo.provider
        ],
    ):
        """
        Interaction w/ DiscAI happens when
          - User sends a regular message in a channel mentioning DiscAI
          - User sends a message in a thread that was created from a previous message
            mentioning DiscAI
        """
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

            # Filter out Discord tags/mentions
            prompt = HumanMessage(strip_mentions(d.message.content))
            stream_t0 = time()
            full_message = ""
            tool_status = ""
            sent_messages: list[Message] = []
            history = [*history, prompt]
            chat_llm = get_chat_model()
            try:
                async for chunk, meta in chat_llm.astream(
                    {"messages": history}, stream_mode="messages"
                ):
                    if meta["langgraph_node"] != "model":
                        continue

                    # Only the first chunk of each streamed tool call carries its name
                    for tc in chunk.tool_call_chunks:
                        if tc["name"]:
                            tool_status = f"Using tool `{tc['name']}`..."

                    if chunk.text:
                        full_message += chunk.text
                        tool_status = ""

                    display = "\n\n".join(filter(None, [full_message, tool_status]))
                    if not display:
                        continue

                    if (
                        not sent_messages
                        or time() - stream_t0 > settings.MESSAGE_EDIT_INTERVAL_SEC
                    ):
                        await render(thread, sent_messages, display)
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
                history.append(AIMessage(full_message))
            except Exception as e:
                await thread.send("An unknown error occurred. Please try again later.")
                logger.exception(e)
                raise

            if not sent_messages:
                raise ValueError("New message not found")

            await render(thread, sent_messages, full_message)

            prompt = HumanMessage("Generate a title for this conversation.")
            title_messages = [
                SystemMessage(settings.TITLE_SYSTEM_PROMPT),
                *history,
                prompt,
            ]
            title_llm = get_title_model()
            if thread.name == settings.NEW_SESSION_TITLE_PLACEHOLDER:
                res = await title_llm.ainvoke(title_messages)
                await thread.edit(name=res.text)
            else:
                should_rename = await jev.should_rename(
                    current_title=thread.name,
                    history=[h.text for h in history],
                )
                if should_rename:
                    res = await title_llm.ainvoke(title_messages)
                    await thread.edit(name=res.text)


async def main():
    container = Container()
    container.wire(modules=[__name__, "src.application.tools.google_search"])
    await container.init_resources()

    try:
        await bot.add_cog(BotCog(bot))
        await bot.start(settings.DISCORD_TOKEN.get_secret_value())
    except Exception as e:  # noqa: BLE001
        logger.exception(e)
    finally:
        await container.shutdown_resources()


if __name__ == "__main__":
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)
    asyncio.run(main())
