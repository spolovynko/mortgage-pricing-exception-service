"""Optional setup checks exercise cache reuse without contacting Ollama."""

import json

from mortgage_pricing.ai import model_init


class Response:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def __iter__(self):
        return iter(self.value.splitlines(keepends=True))

    def __read(self):
        return json.dumps(self.value).encode()

    def read(self):
        return self.__read()


def test_cached_model_skips_pull_and_checks_inference(monkeypatch, capsys):
    calls = []

    def fake_request(_base, endpoint, _payload=None, timeout=30):
        calls.append((endpoint, timeout))
        if endpoint == "/api/tags":
            return Response({"models": [{"name": "demo:1"}]})
        return Response({"response": "OK"})

    monkeypatch.setattr(model_init, "_request", fake_request)
    monkeypatch.setenv("LLM_MODEL", "demo:1")
    assert model_init.main() == 0
    assert [endpoint for endpoint, _ in calls] == ["/api/tags", "/api/tags", "/api/generate"]
    assert "Using cached model" in capsys.readouterr().out
