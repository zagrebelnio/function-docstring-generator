from app.models.parsed import ParsedClass, ParsedFunction
from app.services.parser import parse_source

CODE = (
    "class Repository(Base, Mixin):\n"
    '    """Existing docstring."""\n'
    "\n"
    "    table: str = 'items'\n"
    "    _secret = 'hidden'\n"
    "\n"
    "    def __init__(self, url: str, timeout: float = 5.0) -> None:\n"
    "        self.url = url\n"
    "        self.retries: int = 3\n"
    "        self._cache = {}\n"
    "\n"
    "    def fetch(self, key: str) -> dict:\n"
    "        return {}\n"
)


def parse_class(code: str = CODE) -> ParsedClass:
    symbol = parse_source(code)[0]
    assert isinstance(symbol, ParsedClass)
    return symbol


def test_class_is_returned_before_its_methods():
    symbols = parse_source(CODE)

    assert isinstance(symbols[0], ParsedClass)
    assert [s.qualified_name for s in symbols[1:]] == [
        "Repository.__init__",
        "Repository.fetch",
    ]


def test_class_facts():
    parsed = parse_class()

    assert parsed.name == "Repository"
    assert parsed.bases == ["Base", "Mixin"]
    assert parsed.existing_docstring == "Existing docstring."
    assert parsed.method_names == ["fetch"]


def test_attributes_come_from_body_and_init():
    parsed = parse_class()

    assert [a.name for a in parsed.attributes] == ["table", "url", "retries"]


def test_class_body_attribute_keeps_its_default():
    (table,) = [a for a in parse_class().attributes if a.name == "table"]

    assert table.annotation == "str"
    assert table.default == "'items'"


def test_init_attribute_has_no_default():
    (url,) = [a for a in parse_class().attributes if a.name == "url"]

    assert url.default is None


def test_annotated_init_attribute_keeps_annotation():
    (retries,) = [a for a in parse_class().attributes if a.name == "retries"]

    assert retries.annotation == "int"


def test_private_attributes_are_skipped():
    names = [a.name for a in parse_class().attributes]

    assert "_secret" not in names
    assert "_cache" not in names


def test_nested_class_is_collected():
    code = "class Outer:\n    class Inner:\n        pass"

    names = [s.qualified_name for s in parse_source(code)]

    assert names == ["Outer", "Outer.Inner"]


def test_plain_function_still_parsed_as_function():
    (symbol,) = parse_source("def f(a: int) -> int:\n    return a")

    assert isinstance(symbol, ParsedFunction)
    assert symbol.kind == "function"
