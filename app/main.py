"""Application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_settings
from app.llm import LLMError, build_provider
from app.services.parser import CodeParseError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.llm_provider = build_provider(get_settings())
    except LLMError as exc:
        raise RuntimeError(f"Cannot start: {exc}") from exc
    yield


app = FastAPI(
    title="Function Docstring Generator",
    description="Generates Google and NumPy style docstrings for Python functions.",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(router)
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="ui")


@app.exception_handler(CodeParseError)
async def handle_parse_error(request: Request, exc: CodeParseError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": {"detail": exc.message, "line": exc.line, "offset": exc.offset}},
    )
