"""Style-independent content of a docstring."""

from enum import StrEnum

from pydantic import BaseModel, Field


class DocstringStyle(StrEnum):
    """Supported docstring formats."""

    GOOGLE = "google"
    NUMPY = "numpy"


class DocstringContent(BaseModel):
    """Human-readable descriptions, independent of any docstring format."""

    summary: str
    description: str | None = None
    params: dict[str, str] = Field(default_factory=dict)
    returns: str | None = None
    raises: dict[str, str] = Field(default_factory=dict)
    example: str | None = None
