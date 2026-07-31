"""Provider-agnostic interface to a large language model."""

from abc import ABC, abstractmethod


class LLMError(RuntimeError):
    """Raised when the language model cannot be reached or fails to answer."""


class LLMProvider(ABC):
    """Minimal contract every LLM backend must fulfil."""

    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return the raw text answered by the model."""
