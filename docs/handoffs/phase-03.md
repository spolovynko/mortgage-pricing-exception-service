# Phase 03 handoff - Business rules and API

- Date: 2026-10-29 (Europe/Brussels).
- Status: Complete; MVP1 API workflow implemented and verified. Human acceptance/time are not recorded.
- Git: `615a480` on `main`, one commit ahead of `origin/main`, before these uncommitted acceptance fixes and records. No assistant commit/push.

## Read first

[Project status](../project-status.md), [AGENTS.md](../../AGENTS.md), [ADR 0003](../adr/0003-business-rules-and-api.md), [API contract](../phase-03-api-contract.md), and [Phase 04 guide](../phases/phase-04-user-interface.md).

## Implemented contracts

Create/list/details/history, revisions, exact-version decisions, current approved pricing, and demo user/application lookups are available. The existing Phase 02 operations retain transaction/immutability guarantees. Creation retries return the original version reference; stale/terminal decisions conflict. Only current approved terms are usable.

Enable `DEMO_IDENTITY_MODE=header` and supply a seeded login through `X-Demo-User`; `off` is the default. Both internal roles read all records. Owning managers write; independent reviewers decide. Demo selector bootstrap can use the known fictional `ada.manager` login to fetch identities. This is not authentication.

## Reproduction and verification

Use Python 3.12/uv, `uv sync --locked`, configure a deliberate SQLite path with an existing parent, apply Alembic, then run the seed command. Start the factory with Uvicorn as shown in [README](../../README.md#business-api-phase-03); `/docs` exposes OpenAPI. Fixed seeds contain four fictional users and three applications; seeding creates no requests.

Exact test/check commands, acceptance mapping, and assistant-operated live TCP approval/decline results are in the [build log](../build-log.md#2026-10-29---phase-03-business-rules-api-and-final-acceptance). Tests use temporary file-backed databases; live checks used separate temporary migrated seed storage. No user database was reset.

## Limits and next action

SQLite has bounded lock waits and no automatic retry; lists are unpaginated. UI, containers, and AI are not implemented. Production security, backup, multi-instance behavior, and cross-platform verification remain outside this phase.

Updated: phase guide, ADR/index, build/AI logs, contract, requirements, architecture, implementation plan, README, and status. Next: Phase 04 in its own chat when authorized.
