from typing import Any

from httpx2 import AsyncClient


class SerperRepository:
    def __init__(self, *, client: AsyncClient) -> None:
        self.client = client

    async def search(self, query: str, page: int = 1) -> dict[str, Any]:
        res = await self.client.post(
            "/search",
            json={
                "q": query,
                "hl": "en",
                "gl": "ph",
                "page": page,
            },
        )
        res.raise_for_status()
        return res.json()
