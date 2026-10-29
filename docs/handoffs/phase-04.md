# Phase 04 handoff - User interface

- Date: 2026-10-29 (Europe/Brussels).
- Status: Implemented and verified, including structured-context follow-up; human acceptance/time not recorded.
- Git: `1ca2a75` on `main`; current changes are uncommitted. No commit or push.

## Read first

[Project status](../project-status.md), [Phase 04 guide](../phases/phase-04-user-interface.md), [Phase 05 guide](../phases/phase-05-containerisation.md), [ADR 0009](../adr/0009-single-process-html-ui.md), [ADR 0010](../adr/0010-versioned-request-context.md), [ADR 0003](../adr/0003-business-rules-and-api.md), and the [build evidence](../build-log.md#2026-10-29---phase-04-structured-request-context).

## Implemented and verified

FastAPI serves separate `ui/index.html`, `ui/styles.css`, and `ui/app.js` files and the HTTP API from one Uvicorn process. The browser uses same-origin requests with configured timeout, error envelopes, correlation IDs, demo identity, and idempotency contracts. Identity, roles, rules, decisions, versions, and transaction guarantees remain backend-owned. Request versions retain free text and typed mortgage context; revisions preserve a new snapshot. Synthetic presets fill editable fields but do not write until submitted. Session preferences and creation intent use per-tab `sessionStorage`; assessment generation remains unavailable until Phase 06.

Static-serving/API tests use FastAPI TestClient; browser scenarios used a temporary migrated and seeded SQLite database. They covered structured create/approve/retrieve, revise with a different context/history snapshot, outage/retry with context preserved, and synthetic-prefill no-write behavior. Earlier Phase 04 evidence covers decline/history, separate-tab state, stale review, and filter/toggle no-writes. Windows/CPython 3.12.12 only; no containers, production authentication, model, or human acceptance claimed.

## Reproduce

Use a disposable SQLite path with an existing parent; run `uv run --locked python -m alembic upgrade head`, then `uv run --locked python -m mortgage_pricing.seed`. Set `DEMO_IDENTITY_MODE=header`, configure that same `DATABASE_URL`, and run `uv run --locked uvicorn mortgage_pricing.main:create_app --factory --host 127.0.0.1 --port 8000 --log-config config/logging.json --no-access-log`. Open `http://127.0.0.1:8000/`.

The root `ui/` source is excluded from the Python wheel; include it in the Phase 05 runtime image. ADR 0009 supersedes ADR 0004. Phase 05 must resolve browser routing to the same-origin Uvicorn app alongside its planned API/UI container split. Start Phase 05 only after user authorization.
