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
    DISCORD_TOKEN: SecretStr

    NEW_SESSION_TITLE_PLACEHOLDER: str = "New conversation"
    CHAT_MODEL: str
    TITLE_MODEL: str
    MAX_TOOL_CALLS_PER_TURN: int = Field(5, ge=1, le=10)
    MESSAGE_EDIT_INTERVAL_SEC: int = Field(2, ge=1)
    SYSTEM_PROMPT: str = dedent("""\
    You are a friendly, helpful, general-purpose assistant bot running in Discord.
    Respond with plain text.
    Discord Markdown and code blocks are allowed.
    LaTeX is not supported. If you need to show math equations, use plain characters
    in a code block like so:

    ```
    E^2 = (mc^2)^2 + (pc)^2
    ```

    Tables are also not supported; use the similar code block trick.
    Do not generate images.
    Keep responses below 2000 characters.
    """).strip()
    TITLE_SYSTEM_PROMPT: str = dedent("""\
    Generate a short title for the provided conversation.
    The title must be a very concise summary of the conversation.
    Do not exceed 20 characters.
    Use only plain text. Do not use any special characters.
    """).strip()

    POSTGRESQL_USERNAME: str
    POSTGRESQL_PASSWORD: SecretStr
    POSTGRESQL_DATABASE: str
    DB_HOST: str
    DB_PORT: int

    JEV_TOKEN: SecretStr

    SERPER_API_KEY: SecretStr

    GLOBAL_HTTP_CLIENTS_TIMEOUT_SEC: int = Field(10, gt=0)

    @computed_field
    @property
    def PRODUCTION(self) -> bool:
        return self.PYTHON_ENV == "production"

    @computed_field
    @property
    def SYSTEM_PROMPT_ADDITIONAL_CONTEXT(self) -> str:
        return dedent(f"""\
        When asked about yourself, use the following information:
        - Your name is DiscAI.
        - You are a Discord chat bot developed by GitHub user
          [kvdomingo](https://github.com/kvdomingo).
        - Behind the scenes, you are powered by the `{self.CHAT_MODEL}` large language
          model developed by Google.
        """).strip()

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
def _get_settings() -> Settings:
    return Settings()


settings = _get_settings()
