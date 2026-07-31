import pytest

from app.models.docstring import DocstringContent, DocstringStyle
from app.services.parser import parse_source
from app.services.renderers import get_renderer

CODE = (
    "def read_file(path: str, encoding: str = 'utf-8') -> str:\n"
    "    if not path:\n"
    "        raise ValueError('empty path')\n"
    "    return open(path, encoding=encoding).read()\n"
)

CONTENT = DocstringContent(
    summary="Read a text file.",
    params={"path": "Path to the file.", "encoding": "Text encoding."},
    returns="Contents of the file.",
    raises={"ValueError": "If the path is empty."},
    example=">>> read_file('a.txt')",
)


@pytest.fixture
def function():
    (parsed,) = parse_source(CODE)
    return parsed


def test_google_style(function):
    result = get_renderer(DocstringStyle.GOOGLE).render(function, CONTENT)

    assert result == (
        "Read a text file.\n"
        "\n"
        "Args:\n"
        "    path (str): Path to the file.\n"
        "    encoding (str, optional): Text encoding. Defaults to 'utf-8'.\n"
        "\n"
        "Returns:\n"
        "    str: Contents of the file.\n"
        "\n"
        "Raises:\n"
        "    ValueError: If the path is empty."
    )


def test_numpy_style(function):
    result = get_renderer(DocstringStyle.NUMPY).render(function, CONTENT)

    assert result == (
        "Read a text file.\n"
        "\n"
        "Parameters\n"
        "----------\n"
        "path : str\n"
        "    Path to the file.\n"
        "encoding : str, optional\n"
        "    Text encoding. Defaults to 'utf-8'.\n"
        "\n"
        "Returns\n"
        "-------\n"
        "str\n"
        "    Contents of the file.\n"
        "\n"
        "Raises\n"
        "------\n"
        "ValueError\n"
        "    If the path is empty."
    )


def test_example_is_opt_in(function):
    without = get_renderer(DocstringStyle.GOOGLE).render(function, CONTENT)
    with_example = get_renderer(DocstringStyle.GOOGLE).render(
        function, CONTENT, include_example=True
    )

    assert "Example:" not in without
    assert "Example:" in with_example


def test_generator_uses_yields():
    (function,) = parse_source("def gen(n: int):\n    yield n")
    content = DocstringContent(
        summary="Yield numbers.", params={"n": "How many."}, returns="A number."
    )

    result = get_renderer(DocstringStyle.GOOGLE).render(function, content)

    assert "Yields:" in result
    assert "Returns:" not in result


def test_var_args_keep_their_prefixes():
    (function,) = parse_source("def f(*args, **kwargs):\n    pass")
    content = DocstringContent(
        summary="Do things.", params={"args": "Positional.", "kwargs": "Keyword."}
    )

    result = get_renderer(DocstringStyle.GOOGLE).render(function, content)

    assert "*args:" in result
    assert "**kwargs:" in result
