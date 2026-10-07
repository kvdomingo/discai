from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.settings import settings

engine = create_async_engine(
    url=settings.DATABASE_URL_ASYNC,
    echo=True,
    future=True,
)

session_maker = async_sessionmaker(
    bind=engine,
    autoflush=True,
    autocommit=False,
)


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession]:
    async with session_maker() as session:
        yield session
