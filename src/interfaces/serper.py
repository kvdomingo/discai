from collections.abc import AsyncGenerator

from httpx2 import AsyncClient

from src.settings import settings


async def get_serper_client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        base_url="https://google.serper.dev",
        headers={
            "X-API-KEY": settings.SERPER_API_KEY.get_secret_value(),
            "Content-Type": "application/json",
        },
        http2=True,
    ) as client:
        yield client
