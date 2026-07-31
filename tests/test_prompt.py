import json

from app.services.parser import parse_source
from app.services.prompt import SYSTEM_PROMPT, build_user_prompt

CODE = (
    "def read_file(path: str, encoding: str = 'utf-8') -> str:\n"
    "    if not path:\n"
    "        raise ValueError('empty path')\n"
    "    return open(path, encoding=encoding).read()\n"
)


def parse_one(code: str = CODE):
    (function,) = parse_source(code)
    return function


def test_system_prompt_mentions_json():
    assert "JSON" in SYSTEM_PROMPT


def test_prompt_lists_every_parameter():
    prompt = build_user_prompt(parse_one())

    facts = json.loads(prompt.split("Facts:\n")[1].split("\n\nSource code:")[0])
    assert [p["name"] for p in facts["parameters"]] == ["path", "encoding"]
    assert facts["parameters"][1]["default"] == "'utf-8'"
    assert facts["raises"] == ["ValueError"]


def test_prompt_includes_source_code():
    prompt = build_user_prompt(parse_one())

    assert "def read_file" in prompt


def test_example_is_disabled_by_default():
    assert 'Set "example" to null.' in build_user_prompt(parse_one())


def test_example_can_be_requested():
    prompt = build_user_prompt(parse_one(), include_example=True)

    assert "usage example" in prompt


def test_method_facts_exclude_self():
    function = parse_one("class Repo:\n    def get(self, key: str) -> str:\n        return key")

    facts = json.loads(
        build_user_prompt(function).split("Facts:\n")[1].split("\n\nSource code:")[0]
    )

    assert facts["is_method"] is True
    assert [p["name"] for p in facts["parameters"]] == ["key"]
