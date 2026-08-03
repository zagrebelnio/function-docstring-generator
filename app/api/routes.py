"""HTTP routes of the application."""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import GeneratorDep, SettingsDep
from app.core.config import Settings
from app.models.docstring import DocstringStyle
from app.schemas.generate import GenerateRequest, GenerateResponse
from app.schemas.parse import ErrorResponse, ParseRequest, ParseResponse
from app.services.parser import CodeParseError, parse_source

router = APIRouter()


def _check_code_length(code: str, settings: Settings) -> None:
    if len(code) > settings.max_code_length:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "detail": (
                    f"Source code is too long "
                    f"(got {len(code)} characters, limit {settings.max_code_length})"
                )
            },
        )


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
def parse(request: ParseRequest, settings: SettingsDep) -> ParseResponse:
    """Extract classes, functions and their signatures from the given Python source code."""
    _check_code_length(request.code, settings)

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
async def generate(
    request: GenerateRequest, generator: GeneratorDep, settings: SettingsDep
) -> GenerateResponse:
    """Generate a docstring for every class and function found in the given source code."""
    _check_code_length(request.code, settings)

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

    targets = (
        [symbol for symbol in symbols if not symbol.existing_docstring]
        if request.skip_documented
        else symbols
    )
    if not targets:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"detail": "Every symbol in the given source code is already documented"},
        )

    if len(targets) > settings.max_symbols_per_request:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "detail": (
                    f"Too many symbols to document in one request "
                    f"(found {len(targets)}, limit {settings.max_symbols_per_request})"
                )
            },
        )

    results = [
        await generator.generate(symbol, request.style, include_example=request.include_example)
        for symbol in targets
    ]
    return GenerateResponse(results=results)
