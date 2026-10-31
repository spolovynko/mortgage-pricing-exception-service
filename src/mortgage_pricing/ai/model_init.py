"""Optional Compose-profile model cache setup and inference readiness check."""

import json
import os
import sys
import time
from contextlib import contextmanager
from urllib.error import URLError
from urllib.request import Request, urlopen


@contextmanager
def _request(base: str, endpoint: str, payload: dict | None = None, timeout: float = 30):
    data = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        base.rstrip("/") + endpoint, data=data, headers={"Content-Type": "application/json"}
    )
    with urlopen(request, timeout=timeout) as response:
        yield response


def main() -> int:
    base = os.environ.get("LLM_BASE_URL", "http://ollama:11434")
    model = os.environ.get("LLM_MODEL", "qwen3:4b-instruct-2507-q4_K_M")
    deadline = time.monotonic() + 120
    while True:
        try:
            with _request(base, "/api/tags", timeout=3) as response:
                installed = {item["name"] for item in json.load(response).get("models", [])}
            break
        except (OSError, URLError, TimeoutError):
            if time.monotonic() >= deadline:
                print("Ollama did not become ready within 120 seconds.", file=sys.stderr)
                return 1
            time.sleep(2)

    if model not in installed:
        print(f"Downloading optional model {model}; progress follows.", flush=True)
        try:
            with _request(
                base, "/api/pull", {"name": model, "stream": True}, timeout=3600
            ) as response:
                for line in response:
                    if line.strip():
                        progress = json.loads(line)
                        print(json.dumps(progress), flush=True)
                        if progress.get("error"):
                            raise RuntimeError("Model download failed")
        except (OSError, URLError, TimeoutError, ValueError, RuntimeError) as exc:
            print(f"Optional model setup failed: {type(exc).__name__}.", file=sys.stderr)
            return 1
    else:
        print(f"Using cached model {model}.", flush=True)

    try:
        with _request(base, "/api/tags", timeout=10) as response:
            installed = {item["name"] for item in json.load(response).get("models", [])}
        if model not in installed:
            raise RuntimeError("Selected model is absent after setup")
        with _request(
            base,
            "/api/generate",
            {
                "model": model,
                "prompt": "Reply with OK.",
                "stream": False,
                "think": False,
                "keep_alive": "30m",
                "options": {"num_predict": 8, "temperature": 0, "seed": 7},
            },
            timeout=120,
        ) as response:
            result = json.load(response)
        if not isinstance(result.get("response"), str) or not result["response"].strip():
            raise RuntimeError("Model readiness inference returned no text")
    except (OSError, URLError, TimeoutError, ValueError, RuntimeError) as exc:
        print(f"Optional model readiness check failed: {type(exc).__name__}.", file=sys.stderr)
        return 1
    print(f"Optional model {model} is ready.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
