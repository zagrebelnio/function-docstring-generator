"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.services.generator import DocstringGenerator

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_generator(request: Request) -> DocstringGenerator:
    """Return a generator backed by the provider created once at startup."""
    return DocstringGenerator(request.app.state.llm_provider)


GeneratorDep = Annotated[DocstringGenerator, Depends(get_generator)]
