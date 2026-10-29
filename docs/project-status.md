# Project status

Last updated: 2026-10-29

## Current position

- Repository state: Phase 01 complete; foundation code, final checks, ADR, and handoff are recorded.
- Scaffold placement: documents are present in the active Git working folder; the existing repository title and .gitignore were preserved. No implementation commit was created by the placement task.
- Completed implementation phase: [Phase 01 - Foundation, configuration, logging](phases/phase-01-foundation-config-logging.md), implemented in user-requested Steps 1-8. See [handoff](handoffs/phase-01.md).
- Next action: [Phase 02 - Database and seed data](phases/phase-02-database-and-seed-data.md) in a new implementation chat. Do not continue automatically.
- Project setup: Python 3.12 series, uv 0.11.6, `pyproject.toml` + `uv.lock`, `src/mortgage_pricing/__init__.py`, and ignored `.venv`. Fresh installation, isolated imports, lock consistency, and dependency consistency passed on Windows/CPython 3.12.12.
- Development checks: 48 tests pass in the workspace, a fresh temporary environment, and an invalid external-settings scenario. Ruff lint/format and lock/dependency checks pass. pytest 9.2.0/Ruff 0.17.3; Windows/CPython 3.12.12 only. Tests clear app environment variables and isolate their working directories.
- Configuration: immutable Pydantic Settings and `.env.example` with validated modes, URLs, bounds, and documented precedence; configuration tests pass. It does not connect to a database or model.
- API: `create_app` factory and `GET /health` are implemented; tests and a local Uvicorn request pass. The health response is process liveness only.
- Logging/errors: per-app JSON logger, ASGI tracing, safe diagnostics, and centralized error envelope/handlers. Live 200/404 checks passed from the fresh environment; Step 7 live 500 verification also passed. Unexpected exceptions before response start return a generic correlated 500. Failures after response start are logged/rethrown.
- Business endpoints, UI, Docker, and model implementation: not present. Live-model evaluation is not available.
- Active work time: not recorded; do not infer it from conversation dates.

Documentation scaffold verification on 2026-10-28: 21 Markdown files and 105 relative links passed a static completeness/link/fence check. At that time all eight phase guides were Not started. This historical result does not validate application or model behaviour; see the build log for its scope.

## Phase tracker

| Phase | Status | ADR | Handoff |
| --- | --- | --- | --- |
| 01 | Complete | [ADR 0001](adr/0001-foundation-config-logging.md), Implemented | [Phase 01](handoffs/phase-01.md) |
| 02 | Not started | To be written | To be written |
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
- Database constraints and competing-update strategy: verify in Phase 02/03.
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

Begin Phase 02 only when requested, reading its guide, the Phase 01 handoff, ADR 0001, and Git state first. Phase 02 has not started. Steps 2-7 are committed (`e9358eb` on `main`); Step 8 tests/records are uncommitted. The assistant has made no commits or pushes. The previously suggested middleware directory refactor has not been implemented; existing module boundaries remain focused. Human review/acceptance and active work time are not recorded.
