import json

import pytest

from app.llm import FakeProvider
from app.models.docstring import DocstringStyle
from app.services.generator import DocstringGenerator
from app.services.parser import parse_source

CODE = (
    "def read_file(path: str, encoding: str = 'utf-8') -> str:\n"
    "    if not path:\n"
    "        raise ValueError('empty path')\n"
    "    return open(path, encoding=encoding).read()\n"
)

ANSWER = json.dumps(
    {
        "summary": "Read a text file.",
        "description": None,
        "params": {"path": "Path to the file.", "encoding": "Text encoding to decode with."},
        "returns": "Contents of the file.",
        "raises": {"ValueError": "If the path is empty."},
        "example": None,
    }
)


@pytest.fixture
def function():
    (parsed,) = parse_source(CODE)
    return parsed


async def test_uses_model_answer(function):
    result = await DocstringGenerator(FakeProvider(ANSWER)).generate(
        function, DocstringStyle.GOOGLE
    )

    assert result.degraded is False
    assert "Read a text file." in result.docstring
    assert "Path to the file." in result.docstring


async def test_falls_back_when_provider_is_unavailable(function):
    provider = FakeProvider(fail=True)

    result = await DocstringGenerator(provider).generate(function, DocstringStyle.NUMPY)

    assert result.degraded is True
    assert len(provider.calls) == 1
    assert "path" in result.docstring


async def test_retries_once_on_malformed_json(function):
    provider = FakeProvider("this is not json")

    result = await DocstringGenerator(provider).generate(function, DocstringStyle.GOOGLE)

    assert len(provider.calls) == 2
    assert result.degraded is True


async def test_second_attempt_can_succeed(function):
    class FlakyProvider(FakeProvider):
        async def complete(self, system_prompt: str, user_prompt: str) -> str:
            self.calls.append((system_prompt, user_prompt))
            return "oops" if len(self.calls) == 1 else ANSWER

    result = await DocstringGenerator(FlakyProvider()).generate(function, DocstringStyle.GOOGLE)

    assert result.degraded is False
    assert "Read a text file." in result.docstring


async def test_accepts_answer_wrapped_in_code_fences(function):
    provider = FakeProvider(f"```json\n{ANSWER}\n```")

    result = await DocstringGenerator(provider).generate(function, DocstringStyle.GOOGLE)

    assert result.degraded is False


async def test_invented_parameters_never_reach_the_docstring(function):
    answer = json.dumps({"summary": "Read a file.", "params": {"verbose": "Not a real one."}})

    result = await DocstringGenerator(FakeProvider(answer)).generate(
        function, DocstringStyle.GOOGLE
    )

    assert "verbose" not in result.docstring
    assert "path" in result.docstring


async def test_example_included_only_when_requested(function):
    answer = json.dumps({"summary": "Read a file.", "example": ">>> read_file('a.txt')"})
    generator = DocstringGenerator(FakeProvider(answer))

    without = await generator.generate(function, DocstringStyle.GOOGLE)
    with_example = await generator.generate(function, DocstringStyle.GOOGLE, include_example=True)

    assert "Example:" not in without.docstring
    assert ">>> read_file" in with_example.docstring
