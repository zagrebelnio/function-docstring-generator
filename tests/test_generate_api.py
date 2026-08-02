import json

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_generator
from app.llm import FakeProvider
from app.main import app
from app.services.generator import DocstringGenerator

ANSWER = json.dumps(
    {
        "summary": "Add two numbers.",
        "params": {"a": "First addend.", "b": "Second addend."},
        "returns": "The sum of both arguments.",
    }
)

CODE = "def add(a: int, b: int) -> int:\n    return a + b"


@pytest.fixture
def client():
    app.dependency_overrides[get_generator] = lambda: DocstringGenerator(FakeProvider(ANSWER))
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_generates_google_style(client):
    response = client.post("/generate", json={"code": CODE})

    assert response.status_code == 200
    (result,) = response.json()["results"]
    assert result["style"] == "google"
    assert result["degraded"] is False
    assert "Args:" in result["docstring"]
    assert "First addend." in result["docstring"]


def test_generates_numpy_style(client):
    response = client.post("/generate", json={"code": CODE, "style": "numpy"})

    (result,) = response.json()["results"]
    assert "Parameters\n----------" in result["docstring"]


def test_rejects_unknown_style(client):
    response = client.post("/generate", json={"code": CODE, "style": "sphinx"})

    assert response.status_code == 422


def test_handles_several_symbols(client):
    code = "def a():\n    pass\n\n\ndef b():\n    pass"

    response = client.post("/generate", json={"code": code})

    assert [r["symbol_name"] for r in response.json()["results"]] == ["a", "b"]


def test_reports_invalid_syntax(client):
    response = client.post("/generate", json={"code": "def broken(:"})

    assert response.status_code == 422
    assert response.json()["detail"]["line"] == 1


def test_lists_supported_styles(client):
    response = client.get("/styles")

    assert response.json() == ["google", "numpy"]


def test_generates_for_class_and_its_methods(client):
    code = (
        "class Repo:\n    "
        "table: str = 'items'\n\n    "
        "def get(self, key: str) -> str:\n        "
        "return key"
    )

    response = client.post("/generate", json={"code": code})

    results = response.json()["results"]
    assert [r["kind"] for r in results] == ["class", "function"]
    assert [r["symbol_name"] for r in results] == ["Repo", "Repo.get"]


def test_skip_documented_filters_symbols(client):
    code = 'def a():\n    """Documented."""\n    pass\n\n\ndef b():\n    pass'

    response = client.post("/generate", json={"code": code, "skip_documented": True})

    assert [r["symbol_name"] for r in response.json()["results"]] == ["b"]


def test_skip_documented_rejects_fully_documented_code(client):
    code = 'def a():\n    """Documented."""\n    pass'

    response = client.post("/generate", json={"code": code, "skip_documented": True})

    assert response.status_code == 422


def test_documented_symbols_are_kept_by_default(client):
    code = 'def a():\n    """Documented."""\n    pass\n\n\ndef b():\n    pass'

    response = client.post("/generate", json={"code": code})

    assert [r["symbol_name"] for r in response.json()["results"]] == ["a", "b"]
