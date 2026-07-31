import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_parse_returns_function_facts(client: TestClient):
    response = client.post(
        "/parse", json={"code": "def add(a: int, b: int = 0) -> int:\n    return a + b"}
    )

    assert response.status_code == 200
    (func,) = response.json()["functions"]
    assert func["name"] == "add"
    assert func["return_annotation"] == "int"
    assert [p["name"] for p in func["parameters"]] == ["a", "b"]


def test_parse_rejects_invalid_syntax(client: TestClient):
    response = client.post("/parse", json={"code": "def broken(:"})

    assert response.status_code == 422
    assert response.json()["detail"]["line"] == 1


def test_parse_rejects_code_without_functions(client: TestClient):
    response = client.post("/parse", json={"code": "x = 1"})

    assert response.status_code == 422


def test_parse_rejects_empty_code(client: TestClient):
    response = client.post("/parse", json={"code": ""})

    assert response.status_code == 422
