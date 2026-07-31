"""Orchestrates generation and rendering of docstrings."""

from __future__ import annotations

import json
import logging

from pydantic import BaseModel, ValidationError

from app.llm import LLMError, LLMProvider
from app.models.docstring import DocstringContent, DocstringStyle
from app.models.parsed import ParsedFunction
from app.services.content import build_skeleton, reconcile
from app.services.prompt import RETRY_SUFFIX, SYSTEM_PROMPT, build_user_prompt
from app.services.renderers import get_renderer

logger = logging.getLogger(__name__)


class GeneratedDocstring(BaseModel):
    """A rendered docstring together with the content it was built from."""

    function_name: str
    style: DocstringStyle
    docstring: str
    content: DocstringContent
    degraded: bool = False


class DocstringGenerator:
    """Produces docstrings, falling back to static analysis when the model fails."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def generate(
        self,
        function: ParsedFunction,
        style: DocstringStyle,
        *,
        include_example: bool = False,
    ) -> GeneratedDocstring:
        """Generate a docstring for one function in the requested style."""
        content, degraded = await self._build_content(function, include_example=include_example)

        return GeneratedDocstring(
            function_name=function.qualified_name,
            style=style,
            docstring=get_renderer(style).render(
                function, content, include_example=include_example
            ),
            content=content,
            degraded=degraded,
        )

    async def _build_content(
        self, function: ParsedFunction, *, include_example: bool
    ) -> tuple[DocstringContent, bool]:
        user_prompt = build_user_prompt(function, include_example=include_example)
        system_prompts = (SYSTEM_PROMPT, SYSTEM_PROMPT + RETRY_SUFFIX)

        for attempt, system_prompt in enumerate(system_prompts, start=1):
            try:
                raw = await self._provider.complete(system_prompt, user_prompt)
            except LLMError as exc:
                logger.warning("LLM unavailable for %s: %s", function.qualified_name, exc)
                break

            try:
                generated = parse_model_answer(raw)
            except (ValidationError, json.JSONDecodeError) as exc:
                logger.warning(
                    "Malformed answer for %s (attempt %d): %s",
                    function.qualified_name,
                    attempt,
                    exc,
                )
                continue

            return reconcile(function, generated), False

        return build_skeleton(function), True


def parse_model_answer(raw: str) -> DocstringContent:
    """Parse the model answer, tolerating Markdown code fences around the JSON."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0].strip()

    return DocstringContent.model_validate(json.loads(text))
