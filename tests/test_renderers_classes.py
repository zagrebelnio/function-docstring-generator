import pytest

from app.models.docstring import DocstringContent, DocstringStyle
from app.services.parser import parse_source
from app.services.renderers import get_renderer

CODE = (
    "class Repository:\n"
    "    table: str = 'items'\n"
    "\n"
    "    def __init__(self, url: str) -> None:\n"
    "        self.url = url\n"
)

CONTENT = DocstringContent(
    summary="Store and fetch items.",
    attributes={"table": "Name of the backing table.", "url": "Connection string."},
    example=">>> Repository('sqlite://')",
)


@pytest.fixture
def parsed_class():
    return parse_source(CODE)[0]


def test_google_class(parsed_class):
    result = get_renderer(DocstringStyle.GOOGLE).render(parsed_class, CONTENT)

    assert result == (
        "Store and fetch items.\n"
        "\n"
        "Attributes:\n"
        "    table (str): Name of the backing table.\n"
        "    url: Connection string."
    )


def test_numpy_class(parsed_class):
    result = get_renderer(DocstringStyle.NUMPY).render(parsed_class, CONTENT)

    assert result == (
        "Store and fetch items.\n"
        "\n"
        "Attributes\n"
        "----------\n"
        "table : str\n"
        "    Name of the backing table.\n"
        "url\n"
        "    Connection string."
    )


def test_class_has_no_args_or_returns(parsed_class):
    result = get_renderer(DocstringStyle.GOOGLE).render(parsed_class, CONTENT)

    assert "Args:" not in result
    assert "Returns:" not in result


def test_class_example_is_opt_in(parsed_class):
    renderer = get_renderer(DocstringStyle.GOOGLE)

    without = renderer.render(parsed_class, CONTENT)
    with_example = renderer.render(parsed_class, CONTENT, include_example=True)

    assert "Example:" not in without
    assert ">>> Repository" in with_example
