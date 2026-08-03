from app.core.config import ProviderName, Settings


def test_defaults_to_fake_provider():
    settings = Settings(_env_file=None)

    assert settings.llm_provider is ProviderName.FAKE
    assert settings.openai_api_key == ""


def test_reads_values_from_environment(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1-mini")

    settings = Settings(_env_file=None)

    assert settings.llm_provider is ProviderName.OPENAI
    assert settings.openai_model == "gpt-4.1-mini"
