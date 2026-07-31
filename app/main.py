"""Application entry point."""

from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Function Docstring Generator",
    description="Generates Google and NumPy style docstrings for Python functions.",
    version="0.1.0",
)
app.include_router(router)
