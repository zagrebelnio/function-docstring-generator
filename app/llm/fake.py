"""Deterministic provider used in tests and for running without credentials."""

import json

from .base import LLMError, LLMProvider

DEFAULT_RESPONSE = json.dumps(
    {
        "summary": "Perform the documented operation.",
        "description": None,
        "params": {},
        "returns": "The produced value.",
        "raises": {},
        "example": None,
    }
)


class FakeProvider(LLMProvider):
    """Returns a canned answer instead of calling a real model."""

    def __init__(self, response: str = DEFAULT_RESPONSE, *, fail: bool = False) -> None:
        self._response = response
        self._fail = fail
        self.calls: list[tuple[str, str]] = []

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Record the prompts and return the configured answer."""
        self.calls.append((system_prompt, user_prompt))
        if self._fail:
            raise LLMError("Fake provider was configured to fail")
        return self._response
