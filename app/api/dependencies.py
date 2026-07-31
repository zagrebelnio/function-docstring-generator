"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.llm import build_provider
from app.services.generator import DocstringGenerator

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_generator(settings: SettingsDep) -> DocstringGenerator:
    """Build the generator with the provider selected in the settings."""
    return DocstringGenerator(build_provider(settings))


GeneratorDep = Annotated[DocstringGenerator, Depends(get_generator)]
