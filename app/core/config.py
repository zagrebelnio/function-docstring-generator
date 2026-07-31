"""Application settings loaded from the environment."""

from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderName(StrEnum):
    """Supported LLM backends."""

    OPENAI = "openai"
    FAKE = "fake"


class Settings(BaseSettings):
    """Runtime configuration of the service."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: ProviderName = ProviderName.FAKE

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    llm_timeout: float = 30.0
    llm_temperature: float = 0.2


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings instance."""
    return Settings()
