"""Send a Python file to the running service and print the generated docstrings."""

import json
import sys
import urllib.request
from pathlib import Path

path = sys.argv[1]
style = sys.argv[2] if len(sys.argv) > 2 else "google"
example = "--example" in sys.argv

payload = json.dumps(
    {
        "code": Path(path).read_text(encoding="utf-8"),
        "style": style,
        "include_example": example,
        "skip_documented": "--skip-documented" in sys.argv,
    }
).encode()

request = urllib.request.Request(
    "http://127.0.0.1:8000/generate", payload, {"Content-Type": "application/json"}
)
with urllib.request.urlopen(request) as response:
    for result in json.load(response)["results"]:
        print(f"--- {result['symbol_name']} [{result['kind']}] degraded={result['degraded']}")
        print(result["docstring"], end="\n\n")
