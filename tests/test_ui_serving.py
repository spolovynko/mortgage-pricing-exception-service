from fastapi.testclient import TestClient

from mortgage_pricing.config import Settings
from mortgage_pricing.main import create_app


def test_root_serves_frontend_with_configured_api_timeout(tmp_path) -> None:
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'ui.sqlite'}",
        ui_timeout_seconds=3.5,
    )

    response = TestClient(create_app(settings)).get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert '<meta name="api-timeout-ms" content="3500">' in response.text
    assert 'href="/ui/styles.css"' in response.text
    assert 'src="/ui/app.js"' in response.text


def test_frontend_assets_are_served_and_api_routes_remain_available(tmp_path) -> None:
    app = create_app(Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'ui.sqlite'}"))

    with TestClient(app) as client:
        stylesheet = client.get("/ui/styles.css")
        script = client.get("/ui/app.js")
        health = client.get("/health")

    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")
    assert "@media (max-width: 760px)" in stylesheet.text
    assert script.status_code == 200
    assert script.headers["content-type"].startswith("text/javascript")
    assert '"X-Demo-User"' in script.text
    assert '"X-Correlation-ID"' in script.text
    assert '"Idempotency-Key"' in script.text
    assert "expected_version: openedVersion" in script.text
    assert health.status_code == 200
