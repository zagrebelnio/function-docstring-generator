"""Structured facts extracted from Python source code."""

from enum import StrEnum

from pydantic import BaseModel, Field


class ParameterKind(StrEnum):
    """How a parameter can be passed to the function."""

    POSITIONAL_ONLY = "positional_only"
    POSITIONAL_OR_KEYWORD = "positional_or_keyword"
    VAR_POSITIONAL = "var_positional"
    KEYWORD_ONLY = "keyword_only"
    VAR_KEYWORD = "var_keyword"


class ParsedParameter(BaseModel):
    """A single parameter of a parsed function."""

    name: str
    annotation: str | None = None
    default: str | None = None
    kind: ParameterKind


class ParsedFunction(BaseModel):
    """Everything we can learn about a function without executing it."""

    name: str
    qualified_name: str
    is_async: bool = False
    is_method: bool = False
    is_generator: bool = False
    decorators: list[str] = Field(default_factory=list)
    parameters: list[ParsedParameter] = Field(default_factory=list)
    return_annotation: str | None = None
    returns_value: bool = False
    raises: list[str] = Field(default_factory=list)
    existing_docstring: str | None = None
    lineno: int
    source: str
