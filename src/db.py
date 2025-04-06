from contextlib import asynccontextmanager
from typing import AsyncIterator

from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.settings import settings

engine = create_async_engine(
    url=settings.DATABASE_URL_ASYNC,
    echo=True,
    future=True,
)

session_maker = async_sessionmaker(bind=engine, autoflush=True, autocommit=False)


@asynccontextmanager
async def get_db() -> AsyncIterator[AsyncSession]:
    session = session_maker()
    try:
        yield session
    except Exception as e:
        logger.exception(str(e))
    finally:
        await session.close()
