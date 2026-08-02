"""HTTP routes of the application."""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import GeneratorDep
from app.models.docstring import DocstringStyle
from app.schemas.generate import GenerateRequest, GenerateResponse
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
    """Extract classes, functions and their signatures from the given Python source code."""
    try:
        symbols = parse_source(request.code)
    except CodeParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"detail": exc.message, "line": exc.line, "offset": exc.offset},
        ) from exc

    if not symbols:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"detail": "No classes, functions or methods found in the given source code"},
        )

    return ParseResponse(symbols=symbols)


@router.get("/styles", tags=["system"])
def styles() -> list[str]:
    """List the docstring styles the service can produce."""
    return [style.value for style in DocstringStyle]


@router.post(
    "/generate",
    response_model=GenerateResponse,
    responses={status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse}},
    tags=["generation"],
)
async def generate(request: GenerateRequest, generator: GeneratorDep) -> GenerateResponse:
    """Generate a docstring for every function found in the given source code."""
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

    results = [
        await generator.generate(function, request.style, include_example=request.include_example)
        for function in functions
    ]
    return GenerateResponse(results=results)
