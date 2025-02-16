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
    BASE_PROMPT: str = """
    You are a friendly, helpful assistant. Respond with plain text as much as possible.
    Markdown and code blocks are allowed. Do not generate artifacts.
    """.strip()

    POSTGRESQL_USERNAME: str
    POSTGRESQL_PASSWORD: str
    POSTGRESQL_DATABASE: str
    DB_HOST: str
    DB_PORT: int

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
