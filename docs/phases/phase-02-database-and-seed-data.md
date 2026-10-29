# Phase 02 - Database and seed data

- Status: In progress; execution Step 1 complete, no persistence implementation yet.
- Milestone: MVP1.
- Prerequisite: Phase 01 complete or its unmet criteria explicitly resolved.
- Primary ADR to create: `docs/adr/0002-database-and-seed-data.md`.
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
2. [ ] Add the persistence foundation.
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
