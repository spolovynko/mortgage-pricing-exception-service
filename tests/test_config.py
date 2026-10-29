from pathlib import Path

import pytest
from pydantic import ValidationError

from mortgage_pricing.config import Settings, get_settings


def test_defaults_are_valid_and_safe() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.demo_identity_mode == "off"
    assert settings.llm_mode == "off"
    assert settings.llm_timeout_seconds == 30
    assert settings.sqlite_busy_timeout_seconds == 5
    assert "127.0.0.1" in str(settings.ui_api_url)
    assert "127.0.0.1" in str(settings.llm_base_url)
    assert "password" not in repr(settings)


def test_environment_overrides_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LLM_MODE", "auto")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "0.25")

    settings = get_settings()

    assert settings.app_env == "test"
    assert settings.log_level == "DEBUG"
    assert settings.llm_mode == "auto"
    assert settings.llm_timeout_seconds == 45
    assert settings.sqlite_busy_timeout_seconds == 0.25


def test_explicit_values_override_dotenv_and_defaults(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=test\nLOG_LEVEL=DEBUG\n", encoding="utf-8")

    settings = Settings(_env_file=env_file, app_env="production")

    assert settings.app_env == "production"
    assert settings.log_level == "DEBUG"


def test_configuration_precedence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=test\nLOG_LEVEL=DEBUG\n", encoding="utf-8")
    monkeypatch.setenv("APP_ENV", "production")

    assert Settings().app_env == "production"
    assert Settings().log_level == "DEBUG"
    assert Settings(app_env="development").app_env == "development"


def test_example_file_contains_valid_defaults() -> None:
    example = Path(__file__).resolve().parents[1] / ".env.example"

    assert Settings(_env_file=example) == Settings(_env_file=None)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("APP_ENV", "private-invalid-value-98765"),
        ("LOG_LEVEL", "TRACE"),
        ("DEMO_IDENTITY_MODE", "true"),
        ("LLM_MODE", "on"),
        ("LLM_TIMEOUT_SECONDS", "0"),
        ("LLM_TIMEOUT_SECONDS", "121"),
        ("SQLITE_BUSY_TIMEOUT_SECONDS", "0"),
        ("SQLITE_BUSY_TIMEOUT_SECONDS", "30.1"),
        ("SQLITE_BUSY_TIMEOUT_SECONDS", "nan"),
        ("DATABASE_URL", "mysql://localhost/db"),
        ("UI_API_URL", "file:///private-path"),
        ("LLM_BASE_URL", "not-a-url"),
        ("LLM_TIMEOUT_SECONDS", "nan"),
        ("LLM_TIMEOUT_SECONDS", "inf"),
        ("LLM_MODEL", ""),
        ("LLM_MODEL", "x" * 129),
    ],
)
def test_invalid_environment_settings_fail_without_echoing_values(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert "private-invalid-value-98765" not in str(exc_info.value)


def test_settings_are_immutable() -> None:
    settings = Settings(_env_file=None)

    with pytest.raises(ValidationError):
        settings.app_env = "test"  # type: ignore[misc]
