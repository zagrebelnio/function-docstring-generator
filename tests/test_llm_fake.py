import json

import pytest

from app.llm.base import LLMError
from app.llm.fake import DEFAULT_RESPONSE, FakeProvider


async def test_returns_canned_response():
    provider = FakeProvider()

    result = await provider.complete("system", "user")

    assert json.loads(result) == json.loads(DEFAULT_RESPONSE)


async def test_records_prompts():
    provider = FakeProvider()

    await provider.complete("system", "user")
    await provider.complete("system", "another")

    assert provider.calls == [("system", "user"), ("system", "another")]


async def test_raises_when_configured_to_fail():
    provider = FakeProvider(fail=True)

    with pytest.raises(LLMError):
        await provider.complete("system", "user")
