from typing import Any

from dependency_injector.wiring import Provide, inject
from langchain.tools import tool

from src.dependencies import Container
from src.repositories.serper import SerperRepository


@inject
async def _google_search(
    *,
    query: str,
    serper: SerperRepository = Provide[Container.serper_repo],
) -> dict[str, Any]:
    return await serper.search(query)


@tool
async def google_search(query: str) -> dict[str, Any]:
    """
    Perform a Google web search via Serper.

    :param query: The search query
    :return: A structured object containing organic search results and a knowledge graph
    """
    result = await _google_search(query=query)
    return {
        "knowledge_graph": result.get("knowledgeGraph"),
        "organic": result.get("organic", []),
    }
