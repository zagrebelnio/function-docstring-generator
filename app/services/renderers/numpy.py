"""NumPy style docstring rendering."""

from __future__ import annotations

from app.models.docstring import DocstringContent
from app.models.parsed import ParsedClass, ParsedFunction

from .base import INDENT, DocstringRenderer


class NumpyRenderer(DocstringRenderer):
    """Renders docstrings in the NumPy format."""

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
            blocks.append(self._parameters(function, content))
        if self.has_result(function):
            blocks.append(self._result(function, content))
        if function.raises:
            blocks.append(self._raises(function, content))
        if include_example and content.example:
            blocks.append(self._example(content))

        return "\n\n".join(blocks)

    @staticmethod
    def _heading(title: str) -> str:
        return f"{title}\n{'-' * len(title)}"

    def _parameters(self, function: ParsedFunction, content: DocstringContent) -> str:
        lines = [self._heading("Parameters")]
        for parameter in function.parameters:
            qualifiers = [parameter.annotation] if parameter.annotation else []
            if self.is_optional(parameter):
                qualifiers.append("optional")

            name = self.display_name(parameter)
            lines.append(f"{name} : {', '.join(qualifiers)}" if qualifiers else name)

            text = self.parameter_text(parameter, content)
            lines.append(f"{INDENT}{text}")
        return "\n".join(lines)

    def _result(self, function: ParsedFunction, content: DocstringContent) -> str:
        lines = [self._heading(self.result_section_name(function))]
        if function.return_annotation:
            lines.append(function.return_annotation)
        lines.append(f"{INDENT}{(content.returns or '').strip()}")
        return "\n".join(lines)

    def _raises(self, function: ParsedFunction, content: DocstringContent) -> str:
        lines = [self._heading("Raises")]
        for exception in function.raises:
            lines.append(exception)
            lines.append(f"{INDENT}{content.raises.get(exception, '').strip()}")
        return "\n".join(lines)

    def _example(self, content: DocstringContent) -> str:
        return f"{self._heading('Examples')}\n{content.example.strip()}"

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
        lines = [self._heading("Attributes")]
        for attribute in cls.attributes:
            lines.append(
                f"{attribute.name} : {attribute.annotation}"
                if attribute.annotation
                else attribute.name
            )
            lines.append(f"{INDENT}{content.attributes.get(attribute.name, '').strip()}")
        return "\n".join(lines)
