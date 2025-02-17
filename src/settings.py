from functools import lru_cache
from pathlib import Path

from pydantic import computed_field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    ANTHROPIC_API_KEY: str
    DISCORD_TOKEN: str
    CHAT_MODEL: str = "claude-3-5-haiku-latest"

    POSTGRESQL_USERNAME: str
    POSTGRESQL_PASSWORD: str
    POSTGRESQL_DATABASE: str
    DB_HOST: str
    DB_PORT: int

    @computed_field
    @property
    def BASE_PROMPT(self) -> str:
        return f"""
        You are a friendly, helpful assistant. Respond with plain text.
        Markdown and code blocks are allowed. Do not generate artifacts.
        Keep responses below 2000 characters as much as possible.

        When asked about yourself, respond appropriately given the following information:
        You are a Discord chat bot developed by Kenneth V. Domingo. Behind the scenes, you
        are powered by the {self.CHAT_MODEL} large language model developed by Anthropic.
        """.strip()

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRESQL_USERNAME,
                password=self.POSTGRESQL_PASSWORD,
                host=self.DB_HOST,
                port=self.DB_PORT,
                path=self.POSTGRESQL_DATABASE,
            )
        )


@lru_cache
def _get_settings():
    return Settings()


settings = Settings()
