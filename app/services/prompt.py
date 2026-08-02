"""Prompt construction for docstring generation."""

from __future__ import annotations

import json

from app.models.parsed import ParsedClass, ParsedFunction, ParsedSymbol

SYSTEM_PROMPT = (
    "You are a senior Python engineer writing documentation.\n"
    "You receive the source code of one function or class together with facts extracted "
    "by a static analyser. The facts are authoritative: never document a parameter, "
    "attribute or exception that is not listed, and never skip one that is.\n"
    "Answer with a single JSON object and nothing else, using these keys:\n"
    '  "summary": one sentence under 80 characters, ending with a period\n'
    '  "description": an optional extra paragraph, or null\n'
    '  "params": an object mapping every parameter name to one sentence\n'
    '  "attributes": an object mapping every attribute name to one sentence\n'
    '  "returns": one sentence about the produced value, or null\n'
    '  "raises": an object mapping every exception name to the condition triggering it\n'
    '  "example": a short doctest-style snippet using >>> , or null\n'
    "Describe meaning, not types: the types are already visible in the code.\n"
    'For a class, use "attributes" and leave "params", "returns" and "raises" empty.'
)

RETRY_SUFFIX = "\n\nYour previous answer was not valid JSON. Return only the JSON object."


def build_user_prompt(symbol: ParsedSymbol, *, include_example: bool = False) -> str:
    """Describe one symbol to the model as structured facts plus its source code."""
    example_rule = (
        'Provide a short usage example in "example".'
        if include_example
        else 'Set "example" to null.'
    )
    facts = _class_facts(symbol) if isinstance(symbol, ParsedClass) else _facts(symbol)

    return (
        f"Facts:\n{json.dumps(facts, indent=2)}\n\n"
        f"Source code:\n```python\n{symbol.source}\n```\n\n"
        f"{example_rule}"
    )


def _facts(function: ParsedFunction) -> dict:
    return {
        "kind": "function",
        "name": function.qualified_name,
        "is_async": function.is_async,
        "is_method": function.is_method,
        "is_generator": function.is_generator,
        "parameters": [
            {
                "name": parameter.name,
                "annotation": parameter.annotation,
                "default": parameter.default,
                "kind": parameter.kind.value,
            }
            for parameter in function.parameters
        ],
        "return_annotation": function.return_annotation,
        "returns_value": function.returns_value,
        "raises": function.raises,
    }


def _class_facts(cls: ParsedClass) -> dict:
    return {
        "kind": "class",
        "name": cls.qualified_name,
        "bases": cls.bases,
        "decorators": cls.decorators,
        "attributes": [
            {"name": a.name, "annotation": a.annotation, "default": a.default}
            for a in cls.attributes
        ],
        "public_methods": cls.method_names,
    }
