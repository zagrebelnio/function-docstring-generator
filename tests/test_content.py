from app.models.docstring import DocstringContent
from app.services.content import build_skeleton, reconcile
from app.services.parser import parse_source


def parse_one(code: str):
    (function,) = parse_source(code)
    return function


def test_skeleton_covers_every_parameter():
    function = parse_one("def read_file(path: str, encoding: str = 'utf-8') -> str:\n    return ''")

    skeleton = build_skeleton(function)

    assert skeleton.summary == "Read file."
    assert set(skeleton.params) == {"path", "encoding"}
    assert "str" in skeleton.params["path"]
    assert skeleton.returns is not None


def test_skeleton_has_no_returns_for_void_function():
    function = parse_one("def log(message: str):\n    print(message)")

    assert build_skeleton(function).returns is None


def test_reconcile_drops_invented_parameters():
    function = parse_one("def add(a: int, b: int) -> int:\n    return a + b")
    content = DocstringContent(
        summary="Add numbers.",
        params={"a": "First.", "b": "Second.", "verbose": "Invented by the model."},
        returns="The sum.",
    )

    result = reconcile(function, content)

    assert set(result.params) == {"a", "b"}


def test_reconcile_fills_missing_parameters():
    function = parse_one("def add(a: int, b: int) -> int:\n    return a + b")
    content = DocstringContent(summary="Add numbers.", params={"a": "First."}, returns="The sum.")

    result = reconcile(function, content)

    assert result.params["a"] == "First."
    assert result.params["b"]


def test_reconcile_keeps_only_real_exceptions():
    function = parse_one("def f(x: int):\n    if x:\n        raise ValueError('bad')")
    content = DocstringContent(summary="Do.", raises={"TypeError": "Never happens here."})

    result = reconcile(function, content)

    assert set(result.raises) == {"ValueError"}


def test_reconcile_replaces_empty_summary():
    function = parse_one("def fetch_user(user_id: int) -> dict:\n    return {}")
    content = DocstringContent(summary="   ", returns="")

    result = reconcile(function, content)

    assert result.summary == "Fetch user."
    assert result.returns


def test_class_skeleton_covers_attributes():
    parsed = parse_source("class Repo:\n    table: str = 'items'\n")[0]

    skeleton = build_skeleton(parsed)

    assert skeleton.summary == "Repo."
    assert set(skeleton.attributes) == {"table"}
    assert skeleton.params == {}


def test_reconcile_drops_invented_attributes():
    parsed = parse_source("class Repo:\n    table: str = 'items'\n")[0]
    content = DocstringContent(
        summary="Repo.", attributes={"table": "The table.", "ghost": "Nope."}
    )

    result = reconcile(parsed, content)

    assert set(result.attributes) == {"table"}
