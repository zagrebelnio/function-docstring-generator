"""HTTP routes of the application."""

from fastapi import APIRouter, HTTPException, status

from app.schemas.parse import ErrorResponse, ParseRequest, ParseResponse
from app.services.parser import CodeParseError, parse_source

router = APIRouter()


@router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Report that the service is up."""
    return {"status": "ok"}


@router.post(
    "/parse",
    response_model=ParseResponse,
    responses={status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse}},
    tags=["parsing"],
)
def parse(request: ParseRequest) -> ParseResponse:
    """Extract functions and their signatures from the given Python source code."""
    try:
        functions = parse_source(request.code)
    except CodeParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"detail": exc.message, "line": exc.line, "offset": exc.offset},
        ) from exc

    if not functions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"detail": "No functions or methods found in the given source code"},
        )

    return ParseResponse(functions=functions)
