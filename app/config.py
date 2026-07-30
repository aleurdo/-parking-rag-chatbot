from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "parking_docs"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "parking_booking"
    postgres_user: str = "parking"
    postgres_password: str = "parking_secret"

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "info"

    guardrails_enabled: bool = True

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
