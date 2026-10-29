# Phase 02 - Database and seed data

- Status: In progress; execution Steps 1-2 complete. Step 3 requires the user's instruction.
- Milestone: MVP1.
- Prerequisite: Phase 01 complete or its unmet criteria explicitly resolved.
- Primary ADR: [ADR 0002](../adr/0002-database-and-seed-data.md), Implemented for Step 2 only.
- Handoff to create: `docs/handoffs/phase-02.md`.

## Objective

Create persistent, versioned storage that supports exact-term decisions, history, retries, and later AI assessments without losing data on restart.

## Read first

[AGENTS.md](../../AGENTS.md), [project status](../project-status.md), [requirements](../requirements.md), [architecture](../architecture.md), [engineering guidelines](../python-engineering-guidelines.md), the Phase 01 handoff, and relevant foundation ADRs.

## Scope and expected components

Use SQLAlchemy with SQLite and Alembic migrations. Expected locations are `src/mortgage_pricing/persistence/`, `src/mortgage_pricing/seed.py`, migrations/, and persistence tests. Avoid building unused generic repository abstractions.

## User-gated execution steps

Complete one step at a time. Record its checks, then wait for the user's instruction.

1. [x] Confirm the Phase 01 baseline and persistence boundaries.
2. [x] Add the persistence foundation.
3. [ ] Configure and verify SQLite transactions.
4. [ ] Define users, roles, mortgage applications, and manager ownership.
5. [ ] Define logical requests and immutable submitted versions.
6. [ ] Define decisions and append-only history.
7. [ ] Define caller-scoped idempotency records.
8. [ ] Define and verify atomic operation boundaries.
9. [ ] Create and verify the initial Alembic migration.
10. [ ] Add repeatable synthetic seed data.
11. [ ] Add database readiness without changing process liveness.
12. [ ] Run final verification and complete Phase 02 records and handoff.

### Step 1 evidence - 2026-10-29

- The worktree was clean on `main` at `0bc29a0` before Step 1.
- Inspected the required instructions, Phase 01 handoff, Phase 02 guide, requirements, architecture, engineering guidance, commit guidance, ADR 0001, recent build evidence, actual source, tests, and dependency metadata.
- Actual source confirms that `DATABASE_URL` is validated configuration only. The project has no SQLAlchemy or Alembic dependency, persistence package, migration directory, seed command, database readiness check, or generated database.
- `uv run --locked python -m pytest` passed **48 tests**.
- `uv run --locked python -m ruff check .` passed.
- `uv run --locked python -m ruff format --check .` passed for **35 files**.
- `uv lock --check` passed with **28 resolved packages**. `uv pip check` passed with **29 installed packages checked**.
- Verification used uv 0.11.6, Windows, and CPython 3.12.12.
- No dependency, source, database, migration, seed, API, or configuration behavior changed. All Phase 02 implementation tasks and acceptance criteria remain unchecked.
- Human review or acceptance is not recorded. Active work time is not recorded.
- Next action: Step 2, add the persistence foundation, only after the user's instruction.

### Step 2 evidence - 2026-10-29

- Began from clean `main` at `54e219e`, with Step 1 records committed. Added SQLAlchemy/Alembic dependencies, shared metadata, lazy SQLite engine/session factories, `SQLITE_BUSY_TIMEOUT_SECONDS`, storage ignore rules, and isolated foundation tests. No business model, migration, seed, API wiring, or Step 3 configuration was added.
- Resource factories do not connect or initialize schema/directories. The caller owns disposal after sessions close. Standard session contexts provide basic commit/rollback/closure, with no generic repository wrapper. PostgreSQL URLs remain reserved settings and fail safely in this SQLite-only factory. SQL echo is disabled and bound parameters are hidden in exception text.
- `uv run --locked python -m pytest tests/persistence tests/test_config.py`: **33 passed**. Full `uv run --locked python -m pytest`: **62 passed**, including 11 foundation cases. Initial lint found one long assertion, corrected by formatting; all tests passed on their first runs.
- Ruff lint/format passed (39 formatted files); `uv lock --check` passed (33 packages); `uv pip check` passed (32 installed packages); Alembic CLI reports 1.20.1. SQLAlchemy is 2.0.55. See [build log](../build-log.md) for exact commands and final review.
- Foundation tests use only pytest-owned file-backed SQLite and a test-only probe table. They verify imports/factories without side effects, configured timeout, connection release, save/reopen, rollback/recovery, no implicit commit, database isolation, and safe diagnostic values.
- Limits: foreign-key enforcement and explicit SQLite driver transaction configuration remain Step 3. DDL/savepoint/concurrency guarantees and all Phase 02 acceptance criteria remain unverified. API storage lifecycle wiring belongs to Step 11; migrations belong to Step 9. No normal database was opened/reset. Human review and active work time are not recorded.
- Next action: Step 3 only on user instruction. All implementation tasks below remain unchecked because their complete behavior is still pending.

## Implementation tasks

- [ ] Define users/role membership and mortgage applications with a documented manager-ownership relationship.
- [ ] Define a logical request unique per application, submitted versions, current-version reference, decisions, and history events.
- [ ] Define caller-scoped idempotency storage: key, canonical input fingerprint, and the original creation result/reference.
- [ ] Decide how exact version input and actor/time metadata are preserved through application operations.
- [ ] Define database constraints for relationships, unique version numbers, caller/key uniqueness, and at most one decision per version.
- [ ] Establish explicit session/transaction lifetime and SQLite foreign-key/transaction configuration. Document limitations and lock handling.
- [ ] Create and verify the initial Alembic migration. Do not rely on wiping the database to evolve the schema.
- [ ] Add repeatable seed data: at least two managers, two reviewers, and three clearly fictional applications. Reserve a clean application for the create/approve demo.
- [ ] Optionally include clearly fictional approved/declined examples, with coherent historical versions/events rather than fabricated live decisions.
- [ ] Add database access to core readiness; keep process liveness separate and avoid optional AI dependencies.
- [ ] Add seed/migration operational logs without sensitive record dumps.

## Verification

Apply migrations to an empty temporary file-backed database. Seed twice and verify counts/identities remain stable. Save records, close the process/session, reopen, and verify persistence. Exercise uniqueness and foreign-key failures with the actual database. Verify a failed multi-record transaction leaves no partial business/history rows.

Use a test database per test or isolated test group. Never run destructive persistence tests against the developer/evaluator's normal data file.

## Acceptance criteria

- [ ] A fresh database is created through migrations, and a second migration/setup run is safe.
- [ ] Seed execution is repeatable and preserves existing work.
- [ ] Relationships and critical uniqueness rules are enforced by the database.
- [ ] Decision/history data supports the exact-version requirements without editing earlier submitted terms.
- [ ] Persistence and transaction tests pass against file-backed SQLite.
- [ ] The API reports database readiness accurately and fails safely when storage is unavailable.

## Decision record and handover

Explain schema relationships, the one-logical-request policy, history preservation, SQLite configuration, transaction boundaries, and the seed strategy. Record exact migration/seed commands and known limitations. Update the ADR index, this guide, [build log](../build-log.md), [AI usage](../ai-usage.md), and [project status](../project-status.md); create the handoff using [the template](../handoffs/template.md).

Stop after Phase 02. The next phase implements business operations and their HTTP contracts.
