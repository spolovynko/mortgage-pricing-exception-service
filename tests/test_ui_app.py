from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from mortgage_pricing.config import Settings
from ui import client as ui_client

APP_PATH = Path(__file__).parents[1] / "ui" / "app.py"


class FakeApiClient:
    base_url = "http://fake-api"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self.fail_users = False
        self.requests = []
        self.detail = {}
        self.history = []
        self.posts = []
        self.fail_post_once = False

    def get(self, path: str, *, login: str, params=None):
        self.calls.append((path, login, str(params)))
        if path == "/demo/users":
            if self.fail_users:
                from ui.client import ApiError

                raise ApiError(503, "database_unavailable", "Unavailable", "corr-1")
            return [
                {
                    "id": "1",
                    "login": "ada.manager",
                    "display_name": "Ada Manager",
                    "roles": ["relationship_manager"],
                },
                {
                    "id": "2",
                    "login": "sam.reviewer",
                    "display_name": "Sam Reviewer",
                    "roles": ["reviewer"],
                },
            ]
        if path == "/demo/applications":
            return [{"id": "app-1", "reference": "APP-001", "manager_id": "1"}]
        if path == "/requests":
            return self.requests
        if path == "/requests/request-1":
            return self.detail
        if path == "/requests/request-1/history":
            return self.history
        raise AssertionError(f"Unexpected API read: {path}")

    def request(self, method: str, path: str, *, login: str, json, **kwargs):
        self.posts.append((method, path, login, json, kwargs.get("headers", {}).copy()))
        if self.fail_post_once:
            self.fail_post_once = False
            from ui.client import ApiError

            raise ApiError(None, "backend_unavailable", "Timed out", "corr-timeout")
        return {"request_id": "created-1", "version_number": 1, "replayed": False}


def test_bootstrap_empty_state_and_session_ai_toggle(monkeypatch) -> None:
    fake = FakeApiClient()
    monkeypatch.setattr(ui_client, "configured_client", lambda settings: fake)
    monkeypatch.setattr("mortgage_pricing.config.get_settings", lambda: Settings())
    result = AppTest.from_file(str(APP_PATH)).run()
    assert not result.exception
    assert any("No requests" in item.value for item in result.info)
    assert result.sidebar.toggle[0].label == "Use AI assistance"
    assert result.sidebar.button[0].disabled
    assert any("Phase 06" in item.value for item in result.sidebar.caption)


def test_role_aware_navigation_switches_user_without_writes(monkeypatch) -> None:
    fake = FakeApiClient()
    monkeypatch.setattr(ui_client, "configured_client", lambda settings: fake)
    monkeypatch.setattr("mortgage_pricing.config.get_settings", lambda: Settings())
    result = AppTest.from_file(str(APP_PATH)).run()
    assert result.sidebar.radio[0].options == ["Requests", "History"]
    result.sidebar.selectbox[0].select("Sam Reviewer (sam.reviewer)").run()
    assert any(call[0] == "/requests" and call[1] == "sam.reviewer" for call in fake.calls)
    assert {call[0] for call in fake.calls}.issubset(
        {"/demo/users", "/demo/applications", "/requests"}
    )


def test_backend_error_is_visible(monkeypatch) -> None:
    fake = FakeApiClient()
    fake.fail_users = True
    monkeypatch.setattr(ui_client, "configured_client", lambda settings: fake)
    monkeypatch.setattr("mortgage_pricing.config.get_settings", lambda: Settings())
    result = AppTest.from_file(str(APP_PATH)).run()
    assert any("Unavailable" in item.value for item in result.error)
    assert "corr-1" not in result.error[0].value
    assert result.expander[0].label == "Technical details"


def test_request_summary_exact_terms_and_compact_history(monkeypatch) -> None:
    fake = FakeApiClient()
    fake.requests = [
        {
            "request_id": "request-1",
            "application_id": "app-1",
            "application_reference": "APP-001",
            "current_version_number": 1,
            "status": "pending",
        }
    ]
    version = {
        "version_number": 1,
        "status": "pending",
        "discount_bps": 25,
        "reason": "  Exact submitted reason\nwith a new line.  ",
        "submitted_by_login": "ada.manager",
        "submitted_at": "2026-10-29T12:00:00Z",
        "decision": None,
    }
    fake.detail = {**fake.requests[0], "current_version": version}
    fake.history = [
        {
            "event_type": "created",
            "version_number": 1,
            "actor_login": "ada.manager",
            "occurred_at": "2026-10-29T12:00:00Z",
            "version": version,
        }
    ]
    monkeypatch.setattr(ui_client, "configured_client", lambda settings: fake)
    monkeypatch.setattr("mortgage_pricing.config.get_settings", lambda: Settings())
    result = AppTest.from_file(str(APP_PATH)).run()
    assert not result.exception
    assert list(result.dataframe[0].value.columns) == ["Application", "Status", "Version"]
    assert any(item.value == version["reason"] for item in result.text_area if item.disabled)
    assert "request-1" not in result.selectbox(key="request_selection").value
    result.sidebar.radio[0].set_value("History").run()
    assert not result.exception
    assert result.expander[0].label == "View version 1 terms · created"
    assert any("not a snapshot" in item.value for item in result.caption)


def test_create_retry_reuses_key_and_exact_payload(monkeypatch) -> None:
    fake = FakeApiClient()
    fake.fail_post_once = True
    monkeypatch.setattr(ui_client, "configured_client", lambda settings: fake)
    monkeypatch.setattr("mortgage_pricing.config.get_settings", lambda: Settings())
    result = AppTest.from_file(str(APP_PATH)).run()
    next(item for item in result.selectbox if item.label == "Application").select("APP-001")
    next(item for item in result.text_input if item.label == "Discount (basis points)").set_value(
        "25"
    )
    next(
        item for item in result.text_area if item.label == "Reason (1–2,000 characters)"
    ).set_value("Customer offer")
    next(item for item in result.button if item.label == "Submit request").click().run()
    assert len(fake.posts) == 1
    first_key = fake.posts[0][4]["Idempotency-Key"]
    assert fake.posts[0][3] == {
        "application_id": "app-1",
        "discount_bps": 25,
        "reason": "Customer offer",
    }
    result.button(key="retry_create_ada.manager").click().run()
    assert len(fake.posts) == 2
    assert fake.posts[1][3] == fake.posts[0][3]
    assert fake.posts[1][4]["Idempotency-Key"] == first_key


def test_revision_is_explicit_and_uses_opened_version(monkeypatch) -> None:
    fake = FakeApiClient()
    fake.requests = [
        {
            "request_id": "request-1",
            "application_id": "app-1",
            "application_reference": "APP-001",
            "current_version_number": 1,
            "status": "declined",
        }
    ]
    fake.detail = {
        **fake.requests[0],
        "current_version": {
            "version_number": 1,
            "status": "declined",
            "discount_bps": 25,
            "reason": "Original",
            "submitted_by_login": "ada.manager",
            "submitted_at": "2026-10-29T12:00:00Z",
            "decision": None,
        },
    }
    monkeypatch.setattr(ui_client, "configured_client", lambda settings: fake)
    monkeypatch.setattr("mortgage_pricing.config.get_settings", lambda: Settings())
    result = AppTest.from_file(str(APP_PATH)).run()
    next(
        item for item in result.text_input if item.label == "New discount (basis points)"
    ).set_value("40")
    next(
        item
        for item in result.text_area
        if item.label == "Reason for revised terms (1–2,000 characters)"
    ).set_value("Updated offer")
    next(item for item in result.button if item.label == "Submit revision").click().run()
    assert len(fake.posts) == 1
    assert fake.posts[0][1:] == (
        "/requests/request-1/revisions",
        "ada.manager",
        {"expected_version": 1, "discount_bps": 40, "reason": "Updated offer"},
        {},
    )
