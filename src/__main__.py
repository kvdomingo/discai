import asyncio
import re

from agno.run.response import RunResponse
from discord import Intents, Message
from discord.ext.commands import Bot, Cog
from loguru import logger

from src.agent import get_agent
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
        if self.client.user not in message.mentions:
            return

        async with message.channel.typing():
            agent = get_agent(
                conversation_id=str(message.channel.id),
                user_id=str(message.author.id),
            )
            content = re.sub(r"\s*<@\d+>\s*", "", message.content)
            res: RunResponse = await agent.arun(content)
            await message.reply(res.content)


async def main():
    await bot.add_cog(BotCog(bot))
    await bot.start(settings.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
