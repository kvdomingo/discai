from textwrap import dedent

from loguru import logger
from typesafe_sdk import AsyncTypeSafeClient, Noul, NoulCriteria

from src.models.jev import ShouldRenameResponse


class JevRepository:
    def __init__(self, *, client: AsyncTypeSafeClient) -> None:
        self.client = client
        self.noul_true_threshold: float = 2 / 3

    async def should_rename(
        self, history: list[dict] | list[str], current_title: str
    ) -> bool:
        res = await self.client.system_one(
            state={
                "current_title": current_title,
                "history": history,
            },
            questions={
                "should_rename": Noul(
                    instructions="Should the conversation be renamed?",
                    criteria=NoulCriteria(
                        true=dedent("""\
                        The current title seems to be a placeholder, is too generic, or
                        no longer accurately represents the conversation.
                        """).strip(),
                        false="The current title concisely represents the conversation.",
                    ),
                ),
            },
            response_model=ShouldRenameResponse,
        )

        out = res.should_rename.noul >= self.noul_true_threshold
        logger.debug(
            f"Jev decided to{' ' if out else ' not'} rename (prob={res.should_rename.noul})"
        )
        return out
