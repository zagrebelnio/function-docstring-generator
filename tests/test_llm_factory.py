import pytest

from app.core.config import ProviderName, Settings
from app.llm import FakeProvider, OpenAIProvider, build_provider
from app.llm.base import LLMError


def test_builds_fake_provider_by_default():
    provider = build_provider(Settings(_env_file=None))

    assert isinstance(provider, FakeProvider)


def test_builds_openai_provider_when_selected():
    settings = Settings(_env_file=None, llm_provider=ProviderName.OPENAI, openai_api_key="test-key")

    provider = build_provider(settings)

    assert isinstance(provider, OpenAIProvider)


def test_openai_provider_requires_api_key():
    settings = Settings(_env_file=None, llm_provider=ProviderName.OPENAI, openai_api_key="")

    with pytest.raises(LLMError):
        build_provider(settings)
