# Project status

Last updated: 2026-10-29

## Current position

- Repository state: Phases 01 and 02 are complete. Phase 03 has not started.
- Scaffold placement: documents are present in the active Git working folder; the existing repository title and .gitignore were preserved. No implementation commit was created by the placement task.
- Completed implementation phase: [Phase 01 - Foundation, configuration, logging](phases/phase-01-foundation-config-logging.md), implemented in user-requested Steps 1-8. See [handoff](handoffs/phase-01.md).
- Completed implementation phase: [Phase 02 - Database and seed data](phases/phase-02-database-and-seed-data.md). See [handoff](handoffs/phase-02.md).
- Next action: [Phase 03 - Business rules and API](phases/phase-03-business-rules-and-api.md), only after the user's instruction. Do not continue automatically.
- Project setup: Python 3.12 series, uv 0.11.6, `pyproject.toml` + `uv.lock`, `src/mortgage_pricing/__init__.py`, and ignored `.venv`. Fresh installation, isolated imports, lock consistency, and dependency consistency passed on Windows/CPython 3.12.12.
- Development checks: final Phase 02 workspace suite passes 121 tests, including an isolated migration/seed/restart/readiness acceptance scenario. Ruff lint/format and lock/dependency checks pass (33 locked/32 installed packages). Phase 01's historical fresh-environment and invalid external-settings runs covered its 48-test suite; those scenarios have not been rerun for Phase 02. Windows/CPython 3.12.12 only; tests isolate shell/dotenv settings and working directories.
- Configuration: immutable Pydantic Settings and `.env.example` with validated modes, URLs, bounds, and documented precedence; configuration tests pass. It does not connect to a database or model.
- Persistence foundation: SQLAlchemy 2.0.55, Alembic 1.20.1, shared metadata, lazy engine/session factories, and user/application/request/version/decision/history/idempotency models. Step 3 configures SQLite transactions and foreign keys; Steps 4-7 add core models; Step 8 adds atomic create/revise/decide functions; Step 9 adds Alembic revision `20261029_0001`; Step 10 adds repeatable fictional users/applications; Step 11 adds database readiness. See [ADR 0002](adr/0002-database-and-seed-data.md).
- API: `create_app` factory, process liveness at `GET /health`, and database readiness at `GET /ready` are implemented. Readiness checks an existing SQLite file and current Alembic revision; missing/unmigrated storage returns a safe correlated 503.
- Logging/errors: per-app JSON logger, ASGI tracing, safe diagnostics, and centralized error envelope/handlers. Live 200/404 checks passed from the fresh environment; Step 7 live 500 verification also passed. Unexpected exceptions before response start return a generic correlated 500. Failures after response start are logged/rethrown.
- Business endpoints, UI, Docker, and model implementation: not present. Live-model evaluation is not available.
- Active work time: not recorded; do not infer it from conversation dates.

Documentation scaffold verification on 2026-10-28: 21 Markdown files and 105 relative links passed a static completeness/link/fence check. At that time all eight phase guides were Not started. This historical result does not validate application or model behaviour; see the build log for its scope.

## Phase tracker

| Phase | Status | ADR | Handoff |
| --- | --- | --- | --- |
| 01 | Complete | [ADR 0001](adr/0001-foundation-config-logging.md), Implemented | [Phase 01](handoffs/phase-01.md) |
| 02 | Complete | [ADR 0002](adr/0002-database-and-seed-data.md), Implemented | [Phase 02](handoffs/phase-02.md) |
| 03 | Not started | To be written | To be written |
| 04 | Not started | To be written | To be written |
| 05 | Not started | To be written | To be written |
| 06 | Not started | To be written | To be written |
| 07 | Not started | To be written | To be written |
| 08 | Not started | To be written | To be written |

Allowed phase states: Not started, In progress, Complete, or Incomplete - needs follow-up. Describe any impediment in plain language. Completion must be backed by the guide's acceptance evidence.

## Agreed implementation direction

- Python API with FastAPI; Streamlit UI; SQLite through SQLAlchemy.
- Versioned database changes with Alembic.
- One shared application Dockerfile and one Compose file; separate API and UI containers.
- Optional Ollama and model-initialisation services selected through an `ai` profile.
- Human approval in every operating mode. The UI toggle controls new AI assistance calls.
- Configuration and structured logging are implemented from Phase 01.
- Documentation and commit conventions apply across all phases.

## Decisions still needing implementation detail

- Exact API contracts and validation limits: settle in Phase 01/03 ADRs.
- HTTP mapping for database constraints and competing-update outcomes: settle in Phase 03.
- Settled in Step 2: Python 3.12 series and uv with one project lockfile; see ADR 0001. Final fresh-environment installation and foundation tests pass.
- Settled in Step 4: Pydantic Settings values precedence, accepted configuration modes, defaults, and inert AI/database connection settings; see ADR 0001. Settings construction tests pass.
- Settled in Step 5: minimal FastAPI application factory and process-only `/health` contract. No readiness dependencies are probed.
- Settled in Step 6: JSON log schema, duration in seconds, metadata allowlist, independent handlers, and correlation validation/context.
- Settled in Step 7: safe HTTP/validation error envelope and request-boundary handling of unexpected failures, preserving correlation and standard HTTP headers.
- Settled in Step 8: optional UI stub omitted (UI entry-point location remains `ui/app.py` for Phase 04); application settings/tests are isolated from real shell/dotenv state. No foundation acceptance criteria remain unmet on the tested platform.
- Exact tested Ollama image, model digest, hardware footprint, and latency: establish in Phase 06.
- AI quality criteria and observed judge agreement: establish in Phase 06/07; no accuracy claim yet.

The proposed business policy is in [requirements.md](requirements.md). Record any material change before implementing dependent work.

## Next chat

Start Phase 03 only when requested. Read the Phase 02 handoff, ADR 0002, and the Phase 03 guide before changing code. Human review/acceptance and active work time are not recorded. No assistant commit or push.
