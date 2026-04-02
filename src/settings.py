import os
from functools import lru_cache
from pathlib import Path
from textwrap import dedent
from typing import Literal

from pydantic import Field, PostgresDsn, SecretStr, computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PYTHON_ENV: Literal["development", "production"] = "production"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    GOOGLE_API_KEY: SecretStr = Field(alias="GEMINI_API_KEY")
    GOOGLE_GENAI_USE_VERTEXAI: bool = False
    GOOGLE_CLOUD_PROJECT: str
    GOOGLE_CLOUD_LOCATION: str

    OPENWEATHERMAP_API_KEY: SecretStr
    AGNO_API_KEY: SecretStr
    AGNO_MONITOR: bool
    DISCORD_TOKEN: SecretStr

    NEW_SESSION_TITLE_PLACEHOLDER: str = "New conversation"
    CHAT_MODEL: str = "gemini-3.1-flash-lite-preview"
    TITLE_MODEL: str = "gemini-3.1-flash-lite-preview"
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
    POSTGRESQL_PASSWORD: SecretStr
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
            "password": self.POSTGRESQL_PASSWORD.get_secret_value(),
            "host": self.DB_HOST,
            "port": self.DB_PORT,
            "path": self.POSTGRESQL_DATABASE,
        }

    @computed_field
    @property
    def DATABASE_URL_SYNC(self) -> str:
        return str(
            PostgresDsn.build(
                **self.DATABASE_CONNECTION_PARAMS,  # ty:ignore[invalid-argument-type]
                scheme="postgresql+psycopg2",
            )
        )

    @computed_field
    @property
    def DATABASE_URL_ASYNC(self) -> str:
        return str(
            PostgresDsn.build(
                **self.DATABASE_CONNECTION_PARAMS,  # ty:ignore[invalid-argument-type]
                scheme="postgresql+asyncpg",
            )
        )


@lru_cache
def _get_settings():
    settings = Settings()  # ty:ignore[missing-argument]
    os.environ.setdefault("AGNO_API_KEY", settings.AGNO_API_KEY.get_secret_value())
    os.environ.setdefault("AGNO_MONITOR", str(settings.AGNO_MONITOR).lower())
    return settings


settings = _get_settings()
