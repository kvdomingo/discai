from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Configuration, Factory, Resource

from src.interfaces.db import session_maker
from src.interfaces.jev import get_jev_client
from src.interfaces.serper import get_serper_client
from src.repositories.discord import DiscordRepository
from src.repositories.jev import JevRepository
from src.repositories.querier import Querier
from src.repositories.serper import SerperRepository


class Container(DeclarativeContainer):
    config = Configuration()

    db = Factory(session_maker)
    querier = Factory(Querier, db=db)

    jev_client = Resource(get_jev_client)
    jev_repo = Factory(JevRepository, client=jev_client)

    discord_repo = Factory(DiscordRepository)

    serper_client = Resource(get_serper_client)
    serper_repo = Factory(SerperRepository, client=serper_client)
