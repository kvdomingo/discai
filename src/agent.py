from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.tools.calculator import CalculatorTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.openweather import OpenWeatherTools

from src.settings import settings


def get_agent(conversation_id: str, user_id: str):
    return Agent(
        model=Claude(settings.CHAT_MODEL, api_key=settings.ANTHROPIC_API_KEY),
        name="DiscAI",
        system_message=settings.SYSTEM_PROMPT,
        additional_context=settings.SYSTEM_PROMPT_ADDITIONAL_CONTEXT,
        markdown=True,
        add_name_to_instructions=True,
        add_datetime_to_instructions=True,
        add_history_to_messages=True,
        num_history_responses=10,
        tools=[
            CalculatorTools(enable_all=True),
            DuckDuckGoTools(),
            OpenWeatherTools(api_key=settings.OPENWEATHERMAP_API_KEY),
        ],
        storage=PostgresStorage(
            table_name="agent_sessions",
            db_url=settings.DATABASE_URL_SYNC,
            schema="public",
            auto_upgrade_schema=True,
        ),
        tool_call_limit=5,
        session_id=conversation_id,
        user_id=user_id,
        read_chat_history=True,
        read_tool_call_history=True,
        telemetry=True,
        monitoring=True,
        debug_mode=True,
    )
