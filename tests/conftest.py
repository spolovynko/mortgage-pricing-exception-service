"""Keep tests independent of developer environment variables and local dotenv files."""

import os
from pathlib import Path

import pytest

from mortgage_pricing.config import Settings


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    settings_names = set(Settings.model_fields)
    for name in os.environ:
        if name.lower() in settings_names:
            monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)
