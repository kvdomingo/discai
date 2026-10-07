from collections.abc import AsyncGenerator

from httpx2 import AsyncClient
from typesafe_sdk import AsyncTypeSafeClient, RetryPolicy

from src.settings import settings


async def get_typesafe_client() -> AsyncGenerator[AsyncTypeSafeClient]:
    async with AsyncTypeSafeClient(
        api_key=settings.JEV_TOKEN.get_secret_value(),
        model="jev-latest",
        http_client=AsyncClient(http2=True),
        retry=RetryPolicy(
            max_retries=3, timeout=settings.GLOBAL_HTTP_CLIENTS_TIMEOUT_SEC
        ),
    ) as client:
        yield client
