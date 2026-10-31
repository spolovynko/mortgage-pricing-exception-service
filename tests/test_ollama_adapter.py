"""Offline tests for bounded Ollama request and response handling."""

import asyncio
import json

import pytest

from mortgage_pricing.ai import ollama


def valid_envelope() -> bytes:
    return json.dumps(
        {
            "response": json.dumps(
                {
                    "summary": "Terms submitted.",
                    "reported_claims": [],
                    "missing_information": [],
                    "limitations": ["Claims are unverified; no external evidence checked."],
                }
            )
        }
    ).encode()


def test_valid_response_uses_bounded_output(monkeypatch):
    monkeypatch.setattr(ollama, "_post", lambda *_args: valid_envelope())
    result = asyncio.run(
        ollama.generate_assessment(
            base_url="http://localhost:11434/",
            model="fake",
            timeout=1,
            snapshot={"version_number": 1, "reason": "synthetic"},
        )
    )
    assert result.summary == "Terms submitted."


@pytest.mark.parametrize(
    "snapshot, code",
    [
        ({"reason": "x" * ollama.MAX_INPUT_BYTES}, "input_too_large"),
        ({"version_number": 1}, "malformed_response"),
    ],
)
def test_invalid_input_and_response_fail_safely(monkeypatch, snapshot, code):
    monkeypatch.setattr(ollama, "_post", lambda *_args: b"not-json")
    with pytest.raises(ollama.AssessmentFailure) as error:
        asyncio.run(
            ollama.generate_assessment(
                base_url="http://localhost:11434", model="fake", timeout=1, snapshot=snapshot
            )
        )
    assert error.value.code == code


def test_unavailable_runtime_retries_once(monkeypatch):
    calls = 0

    def unavailable(*_args):
        nonlocal calls
        calls += 1
        raise ollama.AssessmentFailure("runtime_unavailable")

    monkeypatch.setattr(ollama, "_post", unavailable)
    with pytest.raises(ollama.AssessmentFailure, match="runtime_unavailable"):
        asyncio.run(
            ollama.generate_assessment(
                base_url="http://localhost:11434",
                model="fake",
                timeout=1,
                snapshot={"version_number": 1},
            )
        )
    assert calls == 2


def test_stream_disables_thinking_keeps_model_warm_and_returns_latency_metrics(monkeypatch):
    payloads = []
    generated = json.dumps(
        {
            "summary": "Synthetic summary.",
            "reported_claims": [],
            "missing_information": [],
            "limitations": [],
        }
    )

    def fake_stream(_url, payload, _timeout):
        payloads.append(json.loads(payload))
        yield {"response": generated, "done": False}
        yield {
            "response": "",
            "done": True,
            "load_duration": 1_000_000_000,
            "prompt_eval_duration": 500_000_000,
            "eval_duration": 2_000_000_000,
            "eval_count": 40,
        }

    monkeypatch.setattr(ollama, "_stream_response", fake_stream)

    async def run():
        return [
            event
            async for event in ollama.stream_assessment(
                base_url="http://localhost:11434",
                model="fake",
                timeout=1,
                snapshot={"version_number": 1},
            )
        ]

    events = asyncio.run(run())
    assert payloads[0]["think"] is False
    assert payloads[0]["keep_alive"] == "30m"
    assert payloads[0]["options"]["num_predict"] == 512
    assert events[-1]["metrics"] == {
        "load_duration": 1_000_000_000,
        "prompt_eval_duration": 500_000_000,
        "eval_duration": 2_000_000_000,
        "eval_count": 40,
    }
