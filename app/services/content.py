"""Deterministic docstring content derived from static facts only."""

from __future__ import annotations

from app.models.docstring import DocstringContent
from app.models.parsed import ParsedFunction, ParsedParameter

_PLACEHOLDER = "Description is not available."


def humanize(name: str) -> str:
    """Turn an identifier into a readable phrase."""
    return name.strip("_").replace("_", " ").strip()


def build_skeleton(function: ParsedFunction) -> DocstringContent:
    """Build docstring content from the signature alone, without an LLM."""
    return DocstringContent(
        summary=_summary(function),
        params={p.name: _parameter_text(p) for p in function.parameters},
        returns=_returns_text(function),
        raises={exception: _PLACEHOLDER for exception in function.raises},
    )


def reconcile(function: ParsedFunction, content: DocstringContent) -> DocstringContent:
    """Align generated content with the real signature.

    Descriptions for parameters or exceptions that do not exist are dropped, and
    anything the generator missed is filled in from the static skeleton.
    """
    skeleton = build_skeleton(function)

    params = {
        name: (content.params.get(name) or "").strip() or fallback
        for name, fallback in skeleton.params.items()
    }
    raises = {
        exception: (content.raises.get(exception) or "").strip() or fallback
        for exception, fallback in skeleton.raises.items()
    }

    returns = (content.returns or "").strip() or skeleton.returns
    return DocstringContent(
        summary=content.summary.strip() or skeleton.summary,
        description=(content.description or "").strip() or None,
        params=params,
        returns=returns if skeleton.returns is not None else None,
        raises=raises,
        example=(content.example or "").strip() or None,
    )


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
