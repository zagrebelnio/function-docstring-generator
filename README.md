# Function Docstring Generator

A FastAPI service that writes Google or NumPy style docstrings for Python functions.

The service does not hand your code to a language model and hope for the best. It first
analyses the code with Python's own `ast` module, extracts the exact signature, and treats
those facts as the source of truth. The model only supplies prose. The formatting is done
by the service, so the output is always valid for the requested style, and a parameter the
model invents never reaches the result.

## How it works

```
source code
   -> ast analysis          exact parameters, annotations, defaults, raises, yields
   -> prompt                facts + source code, model must answer in JSON
   -> LLM                   descriptions only, one retry if the JSON is malformed
   -> reconcile             invented names dropped, missing ones filled from the signature
   -> renderer              Google or NumPy layout, built by the service
   -> docstring
```

When the model is unreachable, out of quota, or keeps returning broken JSON, the service
falls back to a skeleton built from the signature alone and marks the result with
`degraded: true`. It never fails the request because of the model.

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- An OpenAI API key, optional (see Configuration)

## Quick start

```bash
git clone https://github.com/zagrebelnio/function-docstring-generator.git
cd function-docstring-generator
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API documentation.

The default provider is `fake`, so the service starts and answers without any credentials.
In that mode every docstring comes from static analysis.

## Configuration

All settings are read from environment variables or from a `.env` file.

| Variable          | Default       | Description                                          |
| ----------------- | ------------- | ---------------------------------------------------- |
| `LLM_PROVIDER`    | `fake`        | `openai` for real generation, `fake` for offline use |
| `OPENAI_API_KEY`  | empty         | Required when `LLM_PROVIDER=openai`                  |
| `OPENAI_MODEL`    | `gpt-4o-mini` | Any chat completions model your account can access   |
| `LLM_TIMEOUT`     | `30`          | Request timeout in seconds                           |
| `LLM_TEMPERATURE` | `0.2`         | Lower values give more predictable wording           |

To use a real model:

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Restart the server after editing `.env`.

## API

### `POST /generate`

Generates a docstring for every function and method found in the submitted code.

Request:

```json
{
  "code": "def add(a: int, b: int = 0) -> int:\n    return a + b",
  "style": "google",
  "include_example": false
}
```

| Field             | Type                | Default  | Description                          |
| ----------------- | ------------------- | -------- | ------------------------------------ |
| `code`            | string              | required | Python source, 1 to 20000 characters |
| `style`           | `google` \| `numpy` | `google` | Output format                        |
| `include_example` | boolean             | `false`  | Add a usage example section          |

Response:

```json
{
  "results": [
    {
      "function_name": "add",
      "style": "google",
      "docstring": "Add two numbers.\n\nArgs:\n    a (int): First addend.\n    b (int, optional): Second addend. Defaults to 0.\n\nReturns:\n    int: The sum of both arguments.",
      "content": {
        "summary": "Add two numbers.",
        "description": null,
        "params": { "a": "First addend.", "b": "Second addend." },
        "returns": "The sum of both arguments.",
        "raises": {},
        "example": null
      },
      "degraded": false
    }
  ]
}
```

`content` holds the style independent descriptions the docstring was rendered from.
`degraded` tells you the model was not used and the result comes from static analysis.

JSON strings cannot contain real line breaks, so escape them as `\n` when calling the
endpoint by hand. Sending a whole file is easier:

```bash
python -c "import json;print(json.dumps({'code':open('app/services/parser.py').read()}))" \
  | curl -s -X POST http://127.0.0.1:8000/generate \
      -H "Content-Type: application/json" -d @- \
  | python -m json.tool
```

### `POST /parse`

Returns the facts extracted from the code without calling a model. Useful for inspecting
what the analyser sees: parameter kinds, annotations, defaults, raised exceptions,
generator status, existing docstrings.

### `GET /styles`

Lists the supported docstring styles.

### `GET /health`

Reports that the service is running.

### Errors

Invalid Python, an empty body, or source without a single function returns `422` with a
message and, where the syntax error allows it, the line and column.

## Project structure

```
app/
  api/
    routes.py          HTTP endpoints
    dependencies.py    provider and generator wiring
  core/
    config.py          settings loaded from the environment
  llm/
    base.py            LLMProvider interface and LLMError
    openai.py          OpenAI provider
    fake.py            canned provider for tests and offline use
    __init__.py        build_provider factory
  models/
    parsed.py          facts extracted from source code
    docstring.py       style independent docstring content
  schemas/
    parse.py           request and response models for /parse
    generate.py        request and response models for /generate
  services/
    parser.py          ast analysis
    prompt.py          prompt construction
    content.py         static skeleton and reconciliation with the signature
    generator.py       orchestration, retry, fallback
    renderers/         Google and NumPy layouts
  main.py              application entry point
tests/                 pytest suite
```

## Development

```bash
uv run pytest                  # run the test suite
uv run ruff check .            # lint
uv run ruff format .           # format
uv run pre-commit install      # run both on every commit
```

Tests never call a real model. `FakeProvider` returns canned answers, and the API tests
swap the generator through FastAPI dependency overrides. The suite covers signature
parsing, both renderers, reconciliation against the signature, retry behaviour, and the
fallback path.

GitHub Actions runs the linter, the formatter check, and the tests on every push to
`main` and `develop` and on every pull request.

## Adding a docstring style

Subclass `DocstringRenderer`, implement `render`, and register the class in
`app/services/renderers/__init__.py`. The prompt and the model stay untouched, because the
model never sees the style.
