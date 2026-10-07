from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Configuration, Factory, Singleton
from httpx2 import AsyncClient
from typesafe_sdk import AsyncTypeSafeClient, RetryPolicy

from src.interfaces.db import session_maker
from src.repositories.discord import DiscordRepository
from src.repositories.jev import JevRepository
from src.repositories.querier import Querier
from src.settings import settings


class Container(DeclarativeContainer):
    config = Configuration()

    db = Factory(session_maker)
    querier = Factory(Querier, db=db)
    httpx2_client = Singleton(AsyncClient, http2=True)
    jev_client = Singleton(
        AsyncTypeSafeClient,
        api_key=settings.JEV_TOKEN.get_secret_value(),
        model="jev-latest",
        http_client=httpx2_client,
        retry=RetryPolicy(max_retries=3, timeout=10),
    )
    jev_repo = Factory(JevRepository, client=jev_client)
    discord_repo = Factory(DiscordRepository)
