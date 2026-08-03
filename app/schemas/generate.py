"""Request and response schemas for the generation endpoint."""

from pydantic import BaseModel, Field

from app.models.docstring import DocstringStyle
from app.schemas.parse import HARD_CODE_LENGTH_CEILING
from app.services.generator import GeneratedDocstring


class GenerateRequest(BaseModel):
    """Source code to document, plus the desired output format."""

    code: str = Field(min_length=1, max_length=HARD_CODE_LENGTH_CEILING)
    style: DocstringStyle = DocstringStyle.GOOGLE
    include_example: bool = False
    skip_documented: bool = False


class GenerateResponse(BaseModel):
    """Docstrings generated for every function found in the source code."""

    results: list[GeneratedDocstring]
