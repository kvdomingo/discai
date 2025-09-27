import os
from functools import lru_cache
from pathlib import Path
from textwrap import dedent
from typing import Literal

from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PYTHON_ENV: Literal["development", "production"] = "production"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    ANTHROPIC_API_KEY: str
    GOOGLE_API_KEY: str
    GOOGLE_GENAI_USE_VERTEXAI: bool = False
    GOOGLE_CLOUD_PROJECT: str
    GOOGLE_CLOUD_LOCATION: str
    OPENWEATHERMAP_API_KEY: str
    AGNO_API_KEY: str
    AGNO_MONITOR: bool
    DISCORD_TOKEN: str
    NEW_SESSION_TITLE_PLACEHOLDER: str = "New conversation"
    CHAT_MODEL: str = "gemini-2.5-flash"
    TITLE_MODEL: str = "gemini-2.5-flash"
    SYSTEM_PROMPT: str = dedent("""\
    You are a friendly, helpful, general-purpose assistant.
    Respond with plain text.
    Markdown and code blocks are allowed.
    Do not generate images.
    Keep responses below 2000 characters.
    """).strip()
    TITLE_SYSTEM_PROMPT: str = dedent("""\
    Generate a short title for the provided message.
    The title must be a very concise summary of the message.
    Do not exceed 20 characters.
    Use only plain text. Do not use any special characters.
    """).strip()

    POSTGRESQL_USERNAME: str
    POSTGRESQL_PASSWORD: str
    POSTGRESQL_DATABASE: str
    DB_HOST: str
    DB_PORT: int

    @computed_field
    @property
    def SYSTEM_PROMPT_ADDITIONAL_CONTEXT(self) -> str:
        return dedent(f"""\
        When asked about yourself, use the following metadata:
        - Your name is DiscAI.
        - You are a Discord chat bot developed by GitHub user [kvdomingo](https://github.com/kvdomingo).
        - Behind the scenes, you are powered by the `{self.CHAT_MODEL}` large language model developed by Google.
        """)

    @computed_field
    @property
    def DATABASE_CONNECTION_PARAMS(self) -> dict[str, str | int]:
        return {
            "username": self.POSTGRESQL_USERNAME,
            "password": self.POSTGRESQL_PASSWORD,
            "host": self.DB_HOST,
            "port": self.DB_PORT,
            "path": self.POSTGRESQL_DATABASE,
        }

    @computed_field
    @property
    def DATABASE_URL_SYNC(self) -> str:
        return str(
            PostgresDsn.build(
                **self.DATABASE_CONNECTION_PARAMS,
                scheme="postgresql+psycopg2",
            )
        )

    @computed_field
    @property
    def DATABASE_URL_ASYNC(self) -> str:
        return str(
            PostgresDsn.build(
                **self.DATABASE_CONNECTION_PARAMS,
                scheme="postgresql+asyncpg",
            )
        )


@lru_cache
def _get_settings():
    settings = Settings()
    os.environ.setdefault("AGNO_API_KEY", settings.AGNO_API_KEY)
    os.environ.setdefault("AGNO_MONITOR", str(settings.AGNO_MONITOR).lower())
    return settings


settings = _get_settings()
