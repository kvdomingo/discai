from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Configuration, Factory, Resource

from src.interfaces.postgres import session_maker
from src.interfaces.serper import get_serper_client
from src.interfaces.typesafe import get_typesafe_client
from src.repositories.discord import DiscordMessageRepository
from src.repositories.queriers import AsyncQueriers
from src.repositories.serper import SerperRepository
from src.repositories.typesafe import TypeSafeRepository


class Container(DeclarativeContainer):
    config = Configuration()

    db = Factory(session_maker)
    queriers = Factory(AsyncQueriers, db=db)
    typesafe_client = Resource(get_typesafe_client)
    typesafe_repo = Factory(TypeSafeRepository, client=typesafe_client)
    discord_message_repo = Factory(DiscordMessageRepository)
    serper_client = Resource(get_serper_client)
    serper_repo = Factory(SerperRepository, client=serper_client)
