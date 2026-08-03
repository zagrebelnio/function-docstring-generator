"""Application entry point."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.services.parser import CodeParseError

app = FastAPI(
    title="Function Docstring Generator",
    description="Generates Google and NumPy style docstrings for Python functions.",
    version="0.1.0",
)
app.include_router(router)
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="ui")


@app.exception_handler(CodeParseError)
async def handle_parse_error(request: Request, exc: CodeParseError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": {"detail": exc.message, "line": exc.line, "offset": exc.offset}},
    )
