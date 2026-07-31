"""Docstring renderers for every supported style."""

from app.models.docstring import DocstringStyle

from .base import DocstringRenderer, to_docstring
from .google import GoogleRenderer
from .numpy import NumpyRenderer

_RENDERERS: dict[DocstringStyle, DocstringRenderer] = {
    DocstringStyle.GOOGLE: GoogleRenderer(),
    DocstringStyle.NUMPY: NumpyRenderer(),
}


def get_renderer(style: DocstringStyle) -> DocstringRenderer:
    """Return the renderer registered for the given style."""
    return _RENDERERS[style]


__all__ = ["DocstringRenderer", "get_renderer", "to_docstring"]
