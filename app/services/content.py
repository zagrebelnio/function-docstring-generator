"""Deterministic docstring content derived from static facts only."""

from __future__ import annotations

from app.models.docstring import DocstringContent
from app.models.parsed import (
    ParsedAttribute,
    ParsedClass,
    ParsedFunction,
    ParsedParameter,
    ParsedSymbol,
)

_PLACEHOLDER = "Description is not available."


def humanize(name: str) -> str:
    """Turn an identifier into a readable phrase."""
    return name.strip("_").replace("_", " ").strip()


def build_skeleton(symbol: ParsedSymbol) -> DocstringContent:
    """Build docstring content from the signature alone, without an LLM."""
    if isinstance(symbol, ParsedClass):
        return DocstringContent(
            summary=f"{humanize(symbol.name).capitalize()}.",
            attributes={a.name: _attribute_text(a) for a in symbol.attributes},
        )

    return DocstringContent(
        summary=_summary(symbol),
        params={p.name: _parameter_text(p) for p in symbol.parameters},
        returns=_returns_text(symbol),
        raises={exception: _PLACEHOLDER for exception in symbol.raises},
    )


def reconcile(symbol: ParsedSymbol, content: DocstringContent) -> DocstringContent:
    """Align generated content with the real signature.

    Descriptions for names that do not exist are dropped, and anything the generator
    missed is filled in from the static skeleton.
    """
    skeleton = build_skeleton(symbol)

    return DocstringContent(
        summary=content.summary.strip() or skeleton.summary,
        description=(content.description or "").strip() or None,
        params=_merge(content.params, skeleton.params),
        attributes=_merge(content.attributes, skeleton.attributes),
        returns=(content.returns or "").strip() or skeleton.returns,
        raises=_merge(content.raises, skeleton.raises),
        example=(content.example or "").strip() or None,
    )


def _merge(generated: dict[str, str], skeleton: dict[str, str]) -> dict[str, str]:
    """Keep only the names present in the skeleton, filling the gaps from it."""
    return {
        name: (generated.get(name) or "").strip() or fallback for name, fallback in skeleton.items()
    }


def _attribute_text(attribute: ParsedAttribute) -> str:
    subject = humanize(attribute.name)
    if attribute.annotation:
        return f"The {subject} of type {attribute.annotation}."
    return f"The {subject}."


def _summary(function: ParsedFunction) -> str:
    return f"{humanize(function.name).capitalize()}."


def _parameter_text(parameter: ParsedParameter) -> str:
    subject = humanize(parameter.name)
    if parameter.annotation:
        return f"The {subject} of type {parameter.annotation}."
    return f"The {subject}."


def _returns_text(function: ParsedFunction) -> str | None:
    if not (function.returns_value or function.is_generator or function.return_annotation):
        return None

    verb = "Yields" if function.is_generator else "Returns"
    if function.return_annotation:
        return f"{verb} a value of type {function.return_annotation}."
    return f"{verb} a value."
