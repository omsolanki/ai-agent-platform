"""Centralized configuration for the agent platform."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_name: str = "ai-agent-platform"
    log_level: str = "INFO"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_fallback_model: str = "gpt-3.5-turbo"
    openai_max_tokens: int = 4096
    openai_temperature: float = 0.2

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "agent_platform"
    postgres_user: str = "agent_user"
    postgres_password: str = "agent_password"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "knowledge_base"

    token_budget_per_request: int = 8000
    max_agent_retries: int = 3
    rate_limit_rpm: int = 60

    otel_enabled: bool = True
    otel_service_name: str = "ai-agent-platform"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    prometheus_port: int = 9090

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
