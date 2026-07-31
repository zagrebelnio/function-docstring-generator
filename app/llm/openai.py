"""OpenAI-compatible provider."""

from __future__ import annotations

from openai import APIError, AsyncOpenAI

from .base import LLMError, LLMProvider


class OpenAIProvider(LLMProvider):
    """Talks to an endpoint implementing the OpenAI chat completions API."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        base_url: str | None = None,
        timeout: float = 30.0,
        temperature: float = 0.2,
    ) -> None:
        if not api_key:
            raise LLMError("API key is missing: set OPENAI_API_KEY or use the fake provider")

        self._model = model
        self._temperature = temperature
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Send both prompts to the model and return its raw answer."""
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                temperature=self._temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except APIError as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise LLMError("LLM returned an empty response")

        return content
