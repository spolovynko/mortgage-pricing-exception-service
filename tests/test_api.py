from fastapi.testclient import TestClient

from mortgage_pricing.config import Settings
from mortgage_pricing.main import create_app


def test_health_endpoint_returns_process_liveness() -> None:
    client = TestClient(create_app(Settings(_env_file=None)))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_application_factory_uses_injected_settings_without_sharing_state() -> None:
    first_settings = Settings(_env_file=None, app_env="test")
    second_settings = Settings(_env_file=None, app_env="production")

    first_app = create_app(first_settings)
    second_app = create_app(second_settings)

    assert first_app.state.settings is first_settings
    assert second_app.state.settings is second_settings
    assert first_app.state.settings is not second_app.state.settings
