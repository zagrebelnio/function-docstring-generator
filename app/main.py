"""Application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(
    title="Function Docstring Generator",
    description="Generates Google and NumPy style docstrings for Python functions.",
    version="0.1.0",
)
app.include_router(router)
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="ui")
