# Phase 04 handoff - User interface

- Date: 2026-10-29 (Europe/Brussels).
- Status: Complete; UI implementation and acceptance evidence recorded. Human acceptance/time are not recorded.
- Git: `1ca2a75` on `main`; Phase 04 edits remain uncommitted. No commit or push.

## Read first

[Project status](../project-status.md), [Phase 04 guide](../phases/phase-04-user-interface.md), [Phase 05 guide](../phases/phase-05-containerisation.md), [ADR 0004](../adr/0004-user-interface.md), [ADR 0003](../adr/0003-business-rules-and-api.md), and this handoff's [build evidence](../build-log.md#2026-10-29---phase-04-user-interface-and-final-acceptance).

## Implemented and verified

Root `ui/app.py` and `ui/client.py` deliver Requests, Review, and History over HTTP. Identity, roles, business rules, version decisions, idempotency, and transaction guarantees remain backend-owned. UI timeout is 10 seconds by default and configurable through `UI_TIMEOUT_SECONDS`; base URL uses `UI_API_URL`. Server error envelopes and correlation IDs are preserved. Demo identities are simulated; AI preference is session-scoped and generation remains disabled until Phase 06. Earlier approvals are historical; revised terms need fresh review.

AppTest uses a fake client for session isolation, rerun/no-write, retry-key, failure, and stale-version coverage. Live UI checks used an isolated migrated/seeded SQLite DB for create/approve/retrieve, revision/fresh review/approval, and decline/history. Commands, results, and limits are in the linked build entry. Windows/CPython 3.12.12 only; no containers, model, production authentication, or human acceptance claimed.

## Reproduce and continue

Use a disposable SQLite path with an existing parent; run `uv run --locked python -m alembic upgrade head`, then `uv run --locked python -m mortgage_pricing.seed`. Set `DEMO_IDENTITY_MODE=header` and that same `DATABASE_URL`; start `uv run --locked uvicorn mortgage_pricing.main:create_app --factory --host 127.0.0.1 --port 8000 --log-config config/logging.json --no-access-log`. In another shell set `UI_API_URL=http://127.0.0.1:8000` and run `uv run --locked streamlit run ui/app.py --server.address 127.0.0.1`.

The root `ui/` source is excluded from the Python wheel package list; Phase 05 must copy/include it and dependencies in the shared image. No Phase 04 API contract change was needed. Records updated: guide, ADR/index, architecture, README, build/AI logs, project status, handoff. Next action: begin Phase 05 only after user authorization.
