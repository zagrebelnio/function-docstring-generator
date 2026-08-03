# Function Docstring Generator

A FastAPI service that writes Google or NumPy style docstrings for Python functions,
methods, and classes.

The service does not hand your code to a language model and hope for the best. It first
analyses the code with Python's own `ast` module and treats what it finds there as fact:
exact parameter names, annotations, defaults, raised exceptions, class attributes. The
model only supplies prose. The formatting is done by the service, so the output is always
valid for the requested style, and a parameter or attribute the model invents never
reaches the result.

## How it works

```
source code
   -> ast analysis          exact signature, attributes, defaults, raises, yields
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

Open http://127.0.0.1:8000/ for the web UI, or http://127.0.0.1:8000/docs for the
interactive API documentation.

The default provider is `fake`, so the service starts and answers without any credentials.
In that mode every docstring comes from static analysis.

## Web UI

The service serves a small page at `/` for trying it out without writing JSON by hand.
Paste a function or a class, pick a style, and press **Write docstrings**. A second tab,
**Signature facts**, calls `/parse` and shows exactly what the analyser extracted before
any prose was generated — useful for seeing why a given description looks the way it does.
Results are cached in the browser per code and settings, so switching tabs back and forth
does not re-trigger a model call.

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

Generates a docstring for every class, function, and method found in the submitted code.

Request:

```json
{
  "code": "def add(a: int, b: int = 0) -> int:\n    return a + b",
  "style": "google",
  "include_example": false,
  "skip_documented": false
}
```

| Field             | Type                | Default  | Description                                |
| ----------------- | ------------------- | -------- | ------------------------------------------ |
| `code`            | string              | required | Python source, 1 to 20000 characters       |
| `style`           | `google` \| `numpy` | `google` | Output format                              |
| `include_example` | boolean             | `false`  | Add a doctest-style usage example          |
| `skip_documented` | boolean             | `false`  | Skip symbols that already have a docstring |

Response:

```json
{
  "results": [
    {
      "symbol_name": "add",
      "kind": "function",
      "style": "google",
      "docstring": "Add two numbers.\n\nArgs:\n    a (int): First addend.\n    b (int, optional): Second addend. Defaults to 0.\n\nReturns:\n    int: The sum of both arguments.",
      "content": {
        "summary": "Add two numbers.",
        "description": null,
        "params": { "a": "First addend.", "b": "Second addend." },
        "attributes": {},
        "returns": "The sum of both arguments.",
        "raises": {},
        "example": null
      },
      "degraded": false
    }
  ]
}
```

`kind` is `function` or `class`. `content` holds the style independent descriptions the
docstring was rendered from. `degraded` tells you the model was not used and the result
comes from static analysis alone.

A class and its methods are returned as separate entries, in source order, each with its
own `kind`. A class result uses `attributes` instead of `params` and never has `returns`.

JSON strings cannot contain real line breaks, so escape them as `\n` when calling the
endpoint by hand. Sending a whole file is easier:

```bash
uv run python scripts/try_generate.py path/to/file.py google
```

Add `--example` for usage examples or `--skip-documented` to skip already-documented
symbols.

### `POST /parse`

Returns the facts extracted from the code without calling a model: parameter kinds,
annotations, defaults, raised exceptions, generator status, class bases and attributes,
existing docstrings. This is what the web UI's **Signature facts** tab calls.

### `GET /styles`

Lists the supported docstring styles.

### `GET /health`

Reports that the service is running.

### Errors

Invalid Python, an empty body, or source without a single class, function, or method
returns `422` with a message and, where the syntax error allows it, the line and column.
If `skip_documented` filters out every symbol, the request also returns `422`.

## Development

```bash
uv run pytest                  # run the test suite
uv run ruff check .            # lint
uv run ruff format .           # format
uv run pre-commit install      # run both on every commit
```

Tests never call a real model. `FakeProvider` returns canned answers, and the API tests
swap the generator through FastAPI dependency overrides. The suite covers signature and
class parsing, both renderers for functions and classes, reconciliation against the
signature, retry behaviour, and the fallback path.

GitHub Actions runs the linter, the formatter check, and the tests on every push to
`main` and `develop` and on every pull request.

## Adding a docstring style

Subclass `DocstringRenderer`, implement `render_function` and `render_class`, and register
the class in `app/services/renderers/__init__.py`. The prompt and the model stay
untouched, because the model never sees the style.
