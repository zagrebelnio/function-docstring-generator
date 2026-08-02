import pytest

from app.models.parsed import ParameterKind
from app.services.parser import CodeParseError, parse_source


def test_simple_function():
    code = "def greet(name: str, greeting: str = 'hi') -> str:\n    return f'{greeting}, {name}'"
    (func,) = parse_source(code)

    assert func.name == "greet"
    assert func.return_annotation == "str"
    assert func.returns_value is True
    assert [p.name for p in func.parameters] == ["name", "greeting"]
    assert func.parameters[0].default is None
    assert func.parameters[1].default == "'hi'"


def test_method_drops_self():
    code = "class Service:\n    def run(self, times: int = 1) -> None:\n        pass"
    _, func = parse_source(code)

    assert func.qualified_name == "Service.run"
    assert func.is_method is True
    assert [p.name for p in func.parameters] == ["times"]


def test_staticmethod_keeps_first_parameter():
    code = """class Service:\n
                @staticmethod\n
                def add(self_like: int) -> int:\n
                        return self_like"""
    _, func = parse_source(code)

    assert [p.name for p in func.parameters] == ["self_like"]


def test_parameter_kinds():
    code = "def f(a, /, b, *args, c=1, **kwargs):\n    pass"
    (func,) = parse_source(code)

    kinds = {p.name: p.kind for p in func.parameters}
    assert kinds == {
        "a": ParameterKind.POSITIONAL_ONLY,
        "b": ParameterKind.POSITIONAL_OR_KEYWORD,
        "args": ParameterKind.VAR_POSITIONAL,
        "c": ParameterKind.KEYWORD_ONLY,
        "kwargs": ParameterKind.VAR_KEYWORD,
    }


def test_async_generator_and_raises():
    code = (
        "async def stream(limit: int):\n"
        "    if limit < 0:\n"
        "        raise ValueError('negative')\n"
        "    yield limit\n"
    )
    (func,) = parse_source(code)

    assert func.is_async is True
    assert func.is_generator is True
    assert func.raises == ["ValueError"]


def test_nested_function_is_ignored():
    code = "def outer():\n    def inner():\n        yield 1\n    return inner"
    (func,) = parse_source(code)

    assert func.name == "outer"
    assert func.is_generator is False


def test_existing_docstring_is_detected():
    code = 'def f():\n    """Already documented."""\n    pass'
    (func,) = parse_source(code)

    assert func.existing_docstring == "Already documented."


def test_invalid_syntax():
    with pytest.raises(CodeParseError) as exc_info:
        parse_source("def broken(:\n    pass")

    assert exc_info.value.line == 1


def test_empty_source():
    with pytest.raises(CodeParseError):
        parse_source("   ")
