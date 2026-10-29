from __future__ import annotations

import pytest

from ui.client import ApiClient, ApiError


class FakeResponse:
    def __init__(
        self, status_code: int, payload: object, correlation_id: str = "server-id"
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.headers = {"X-Correlation-ID": correlation_id}

    def json(self) -> object:
        return self._payload


class FakeTransport:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, str, dict]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append((method, url, kwargs))
        return self.response


def test_client_sends_demo_identity_and_correlation_id() -> None:
    transport = FakeTransport(FakeResponse(200, {"ok": True}))
    client = ApiClient("http://api:8000/", transport=transport)

    assert client.request("GET", "/health", login="ada.manager") == {"ok": True}
    method, url, options = transport.calls[0]
    assert (method, url) == ("GET", "http://api:8000/health")
    assert options["headers"]["X-Demo-User"] == "ada.manager"
    assert options["headers"]["X-Correlation-ID"]


def test_client_preserves_error_envelope_and_server_correlation_id() -> None:
    transport = FakeTransport(
        FakeResponse(
            409,
            {
                "error": {"code": "stale_version", "message": "Refresh."},
                "correlation_id": "body-id",
            },
        )
    )

    with pytest.raises(ApiError) as raised:
        ApiClient("http://api:8000", transport=transport).request(
            "POST", "/requests/id/decisions", login="sam.reviewer"
        )
    assert raised.value.status_code == 409
    assert raised.value.code == "stale_version"
    assert raised.value.correlation_id == "body-id"


def test_client_maps_transport_failure_to_unavailable() -> None:
    class BrokenTransport:
        def request(self, method: str, url: str, **kwargs: object) -> object:
            raise __import__("httpx2").TimeoutException("slow")

    with pytest.raises(ApiError, match="unavailable") as raised:
        ApiClient("http://api:8000", transport=BrokenTransport()).request(
            "GET", "/ready", login="ada.manager"
        )
    assert raised.value.status_code is None
    assert raised.value.correlation_id
