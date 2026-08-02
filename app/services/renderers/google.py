"""Google style docstring rendering."""

from __future__ import annotations

from app.models.docstring import DocstringContent
from app.models.parsed import ParsedClass, ParsedFunction

from .base import INDENT, DocstringRenderer


class GoogleRenderer(DocstringRenderer):
    """Renders docstrings in the Google format."""

    def render_function(
        self,
        function: ParsedFunction,
        content: DocstringContent,
        *,
        include_example: bool = False,
    ) -> str:
        blocks: list[str] = [content.summary.strip()]

        if content.description:
            blocks.append(content.description.strip())
        if function.parameters:
            blocks.append(self._args(function, content))
        if self.has_result(function):
            blocks.append(self._result(function, content))
        if function.raises:
            blocks.append(self._raises(function, content))
        if include_example and content.example:
            blocks.append(self._example(content))

        return "\n\n".join(blocks)

    def _args(self, function: ParsedFunction, content: DocstringContent) -> str:
        lines = ["Args:"]
        for parameter in function.parameters:
            name = self.display_name(parameter)
            qualifiers = [parameter.annotation] if parameter.annotation else []
            if self.is_optional(parameter):
                qualifiers.append("optional")

            head = f"{name} ({', '.join(qualifiers)})" if qualifiers else name
            text = content.params.get(parameter.name, "").strip()
            if self.is_optional(parameter):
                text = f"{text} Defaults to {parameter.default}.".strip()

            lines.append(f"{INDENT}{head}: {text}")
        return "\n".join(lines)

    def _result(self, function: ParsedFunction, content: DocstringContent) -> str:
        head = function.return_annotation or ""
        text = (content.returns or "").strip()
        body = f"{head}: {text}" if head else text
        return f"{self.result_section_name(function)}:\n{INDENT}{body}"

    def _raises(self, function: ParsedFunction, content: DocstringContent) -> str:
        lines = ["Raises:"]
        for exception in function.raises:
            lines.append(f"{INDENT}{exception}: {content.raises.get(exception, '').strip()}")
        return "\n".join(lines)

    def _example(self, content: DocstringContent) -> str:
        body = "\n".join(f"{INDENT}{line}" for line in content.example.strip().splitlines())
        return f"Example:\n{body}"

    def render_class(
        self,
        cls: ParsedClass,
        content: DocstringContent,
        *,
        include_example: bool = False,
    ) -> str:
        blocks: list[str] = [content.summary.strip()]

        if content.description:
            blocks.append(content.description.strip())
        if cls.attributes:
            blocks.append(self._attributes(cls, content))
        if include_example and content.example:
            blocks.append(self._example(content))

        return "\n\n".join(blocks)

    def _attributes(self, cls: ParsedClass, content: DocstringContent) -> str:
        lines = ["Attributes:"]
        for attribute in cls.attributes:
            if attribute.annotation:
                head = f"{attribute.name} ({attribute.annotation})"
            else:
                head = attribute.name
            lines.append(f"{INDENT}{head}: {content.attributes.get(attribute.name, '').strip()}")
        return "\n".join(lines)
