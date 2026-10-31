"""Streaming assessments are validated and persisted only after completion."""

from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from mortgage_pricing.api import assessments
from mortgage_pricing.config import Settings
from mortgage_pricing.main import create_app
from mortgage_pricing.persistence.database import create_session_factory
from mortgage_pricing.persistence.models import PricingAssessment
from mortgage_pricing.seed import seed_database
from tests.test_api_workflow import create

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def live_client(tmp_path: Path) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    settings = Settings(
        _env_file=None,
        demo_identity_mode="header",
        llm_mode="auto",
        database_url=f"sqlite:///{(tmp_path / 'stream.db').as_posix()}",
    )
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
    seed_database(settings)
    client = TestClient(create_app(settings))
    try:
        yield client, create_session_factory(client.app.state.database_engine)
    finally:
        client.close()


def test_stream_returns_structured_narrative_then_persists_checklist(live_client, monkeypatch):
    client, sessions = live_client
    request_id = create(client)
    calls = 0

    async def fake_stream(**_kwargs):
        nonlocal calls
        calls += 1
        from mortgage_pricing.ai.assessment_contract import EvidenceSelection

        result = EvidenceSelection(selected_source_refs=["reason", "discount_bps"])
        yield {"type": "partial", "result": result}
        yield {
            "type": "complete",
            "result": result,
            "metrics": {"ttft_ms": 150, "total_ms": 700},
        }

    monkeypatch.setattr(assessments, "stream_assessment", fake_stream)
    response = client.post(
        f"/requests/{request_id}/assessments/stream",
        headers={"X-Demo-User": "blake.reviewer"},
        json={"expected_version": 1},
    )
    assert response.status_code == 200
    assert (
        "event: context" in response.text
        and "event: partial" in response.text
        and "event: complete" in response.text
    )
    assert "event: metrics" in response.text
    repeated = client.post(
        f"/requests/{request_id}/assessments/stream",
        headers={"X-Demo-User": "blake.reviewer"},
        json={"expected_version": 1},
    )
    assert repeated.status_code == 200 and "event: complete" in repeated.text
    assert calls == 1
    import json

    first_result = response.text.split("event: complete\ndata: ", 1)[1].split("\n", 1)[0]
    cached_result = repeated.text.split("event: complete\ndata: ", 1)[1].split("\n", 1)[0]
    assert json.loads(first_result)["assessment_id"] == json.loads(cached_result)["assessment_id"]
    with sessions() as session:
        stored = session.scalar(
            select(PricingAssessment).where(PricingAssessment.request_id == UUID(request_id))
        )
        assert stored is not None and stored.result["suggested_outcome"] == "suggest_do_not_approve"
        assert stored.prompt_version == assessments.PROMPT_VERSION
