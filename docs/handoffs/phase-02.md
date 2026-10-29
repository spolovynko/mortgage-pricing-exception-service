# Phase 02 handoff - Database and seed data

- Date: 2026-10-29 (Europe/Brussels).
- Phase status: Complete.
- Milestone: MVP1.
- Current commit/branch: `6d743d7` on `main` before the uncommitted Step 12 completion records.

## Read first

Read [project status](../project-status.md), [AGENTS.md](../../AGENTS.md), this handoff, [ADR 0002](../adr/0002-database-and-seed-data.md), and the [Phase 03 guide](../phases/phase-03-business-rules-and-api.md).

## Implemented outcome

SQLite persistence is available through SQLAlchemy with explicit transaction handling, foreign keys, a bounded busy timeout, and no global engine/session. Alembic revision `20261029_0001` creates the schema and SQLite triggers prevent direct mutation of submitted versions, decisions, history, and idempotency records.

The persistence operations create, revise, and decide exact request versions atomically. They enforce manager ownership, reviewer role, no self-review, expected-current-version checks, final decisions, and caller-scoped idempotent creation. `uv run --locked python -m mortgage_pricing.seed` adds stable fictional baseline users/applications after migration, without overwriting collisions or fabricating decisions. `GET /ready` checks an existing migrated SQLite file; `/health` remains independent process liveness.

## Verification performed

| Command or scenario | Observed outcome | Limitations |
| --- | --- | --- |
| `uv run --locked python -m pytest tests/test_phase_02_acceptance.py -q` | 1 passed: migration twice, seed twice, restart persistence, readiness | One isolated SQLite scenario |
| `uv run --locked python -m pytest -q` | 121 passed | Windows/CPython 3.12.12 only |
| Ruff, lock, dependency, and diff checks | All passed; 58 files formatted, 33 locked/32 installed packages | Not a deployment or cross-platform check |
| Existing persistence/migration/seed/readiness tests | Database constraints, direct-SQL immutability, atomic rollback, seed collision/repeatability, safe unavailable storage | No business HTTP endpoints yet |

## Decisions and rationale

[ADR 0002](../adr/0002-database-and-seed-data.md) records the SQLAlchemy/SQLite/Alembic boundary, exact-version relationships, SQLite-specific locking, migration triggers, seed collision policy, and separate readiness/liveness signals. Step 12 selected a compact end-to-end acceptance test rather than duplicating every focused constraint test.

## Unfinished work and known issues

All Phase 02 acceptance criteria have observed test evidence. Human review/acceptance and active work time are not recorded. SQLite is the implemented backend; it has no automatic lock retry, production backup/recovery plan, multi-instance guarantee, or tamper-proof audit claim. `alembic check` is not acceptance evidence because SQLite reflection reports false unique-constraint differences. Phase 03 must define HTTP contracts and map persistence/business failures without expanding Phase 02.

## Environment and reproducibility

Use Python 3.12 and uv 0.11.6. Run `uv sync --locked`, then `uv run --locked python -m alembic upgrade head` and `uv run --locked python -m mortgage_pricing.seed` against a deliberately configured SQLite path. Seeds are two relationship managers, two reviewers, and three `SYN-MORTGAGE-*` applications; `SYN-MORTGAGE-DEMO-CLEAN` intentionally has no request. Tests create their own temporary SQLite files. No live AI was tested.

## Records updated

- Phase guide checkboxes: all Phase 02 execution, task, and acceptance items.
- ADR and ADR index: ADR 0002 marked Implemented.
- Build log and actual time: final commands/outcomes appended; active time not recorded.
- AI usage record: Step 12 contribution and limits appended.
- Project status: Phase 02 Complete; Phase 03 next.
- Requirements/architecture, if changed: architecture and README corrected to the completed implementation state; requirements behavior did not change.

## Next action

Start Phase 03 only when requested. Preserve Phase 02 behavior and its isolated test-database practice. Do not silently begin later phases.
