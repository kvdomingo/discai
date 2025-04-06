from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.tools.calculator import CalculatorTools
from agno.tools.duckduckgo import DuckDuckGoTools

from src.settings import settings

agent = Agent(
    model=Claude(settings.CHAT_MODEL, api_key=settings.ANTHROPIC_API_KEY),
    name="DiscAI",
    system_message=settings.BASE_PROMPT,
    markdown=True,
    add_name_to_instructions=True,
    add_datetime_to_instructions=True,
    tools=[
        CalculatorTools(enable_all=True),
        DuckDuckGoTools(),
    ],
    storage=PostgresStorage(
        table_name="agent_sessions",
        db_url=settings.DATABASE_URL_ASYNC,
        auto_upgrade_schema=True,
    ),
    show_tool_calls=True,
)
