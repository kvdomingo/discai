from textwrap import dedent

from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain.chat_models import BaseChatModel, init_chat_model
from langchain_core.messages import SystemMessage

from src.application.tools.google_search import google_search
from src.settings import settings


def get_chat_model():
    return create_agent(
        init_chat_model(f"google_genai:{settings.CHAT_MODEL}"),
        tools=[google_search],
        middleware=[
            ToolCallLimitMiddleware(run_limit=settings.MAX_TOOL_CALLS_PER_TURN)
        ],
        system_prompt=SystemMessage(
            dedent(f"""
            {settings.SYSTEM_PROMPT}

            {settings.SYSTEM_PROMPT_ADDITIONAL_CONTEXT}
            """).strip()
        ),
    )


def get_title_model() -> BaseChatModel:
    return init_chat_model(f"google_genai:{settings.TITLE_MODEL}")
