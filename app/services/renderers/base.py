"""Shared behaviour for all docstring renderers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.docstring import DocstringContent
from app.models.parsed import (
    ParameterKind,
    ParsedClass,
    ParsedFunction,
    ParsedParameter,
    ParsedSymbol,
)

INDENT = "    "

_PREFIXES = {
    ParameterKind.VAR_POSITIONAL: "*",
    ParameterKind.VAR_KEYWORD: "**",
}


class DocstringRenderer(ABC):
    """Turns style-independent content into formatted docstring text."""

    def render(
        self,
        symbol: ParsedSymbol,
        content: DocstringContent,
        *,
        include_example: bool = False,
    ) -> str:
        """Return the docstring body, without the surrounding triple quotes."""
        if isinstance(symbol, ParsedClass):
            return self.render_class(symbol, content, include_example=include_example)
        return self.render_function(symbol, content, include_example=include_example)

    @abstractmethod
    def render_function(
        self,
        function: ParsedFunction,
        content: DocstringContent,
        *,
        include_example: bool = False,
    ) -> str:
        """Return the docstring body for a function or method."""

    @abstractmethod
    def render_class(
        self,
        cls: ParsedClass,
        content: DocstringContent,
        *,
        include_example: bool = False,
    ) -> str:
        """Return the docstring body for a class."""

    @staticmethod
    def display_name(parameter: ParsedParameter) -> str:
        """Return the parameter name as it should appear in a docstring."""
        return f"{_PREFIXES.get(parameter.kind, '')}{parameter.name}"

    @staticmethod
    def is_optional(parameter: ParsedParameter) -> bool:
        """Tell whether the parameter may be omitted by the caller."""
        return parameter.default is not None

    @staticmethod
    def result_section_name(function: ParsedFunction) -> str:
        """Return the name of the section describing what the function produces."""
        return "Yields" if function.is_generator else "Returns"

    @staticmethod
    def has_result(function: ParsedFunction) -> bool:
        """Tell whether the function produces a value worth documenting."""
        return function.returns_value or function.is_generator or bool(function.return_annotation)


def to_docstring(body: str, indent: int = 4) -> str:
    """Wrap a rendered body in triple quotes and indent it for insertion into code."""
    pad = " " * indent
    lines = body.splitlines()
    if len(lines) == 1:
        return f'{pad}"""{lines[0]}"""'

    inner = "\n".join(f"{pad}{line}".rstrip() for line in lines)
    return f'{pad}"""{lines[0]}\n' + "\n".join(inner.splitlines()[1:]) + f'\n{pad}"""'
