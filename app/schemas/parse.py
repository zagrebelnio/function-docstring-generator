"""Request and response schemas for the parsing endpoint."""

from pydantic import BaseModel, Field

from app.models.parsed import ParsedFunction

MAX_CODE_LENGTH = 20_000


class ParseRequest(BaseModel):
    """Incoming Python source code to analyse."""

    code: str = Field(min_length=1, max_length=MAX_CODE_LENGTH)


class ParseResponse(BaseModel):
    """Functions discovered in the submitted source code."""

    functions: list[ParsedFunction]


class ErrorResponse(BaseModel):
    """Details about source code that could not be parsed."""

    detail: str
    line: int | None = None
    offset: int | None = None
