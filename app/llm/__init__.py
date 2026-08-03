"""LLM provider registry."""

from app.core.config import ProviderName, Settings

from .base import LLMError, LLMProvider
from .fake import FakeProvider
from .openai import OpenAIProvider


def build_provider(settings: Settings) -> LLMProvider:
    """Create the provider selected in the settings."""
    if settings.llm_provider is ProviderName.OPENAI:
        return OpenAIProvider(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            timeout=settings.llm_timeout,
            temperature=settings.llm_temperature,
        )

    return FakeProvider()


__all__ = ["FakeProvider", "LLMError", "LLMProvider", "OpenAIProvider", "build_provider"]
