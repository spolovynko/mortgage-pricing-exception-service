# Project status

Last updated: 2026-10-29

## Current position

- Repository state: Phase 01 in progress; Steps 2-6 are implemented and verified, including structured logging and request correlation.
- Scaffold placement: documents are present in the active Git working folder; the existing repository title and .gitignore were preserved. No implementation commit was created by the placement task.
- Current implementation phase: [Phase 01 - Foundation, configuration, logging](phases/phase-01-foundation-config-logging.md), proceeding one user-requested step at a time. Steps 1-6 are complete; unhandled error responses remain pending.
- Next action: Step 7 - consistent, safe error responses. Do not continue automatically.
- Project setup: Python 3.12 series, uv 0.11.6, `pyproject.toml` + `uv.lock`, `src/mortgage_pricing/__init__.py`, and ignored `.venv`. Fresh installation, isolated imports, lock consistency, and dependency consistency passed on Windows/CPython 3.12.12.
- Development checks: pytest 9.2.0 and Ruff 0.17.3 in the locked `dev` group; test discovery/strictness and lint/format configuration in `pyproject.toml`. One packaging integration test passed; lint/format/lock/dependency checks passed on Windows/CPython 3.12.12.
- Configuration: immutable Pydantic Settings and `.env.example` with validated modes, URLs, bounds, and documented precedence; configuration tests pass. It does not connect to a database or model.
- API: `create_app` factory and `GET /health` are implemented; tests and a local Uvicorn request pass. The health response is process liveness only.
- Logging: per-app JSON logger, ASGI request tracing, bounded correlation IDs, and safe diagnostics. 28 tests pass, including 14 logging cases; live 200/404 responses and JSON logs match. Unhandled 500 correlation headers/error envelopes remain Step 7 work.
- Business endpoints, UI, Docker, and model implementation: not present. Live-model evaluation is not available.
- Active work time: not recorded; do not infer it from conversation dates.

Documentation scaffold verification on 2026-10-28: 21 Markdown files and 105 relative links passed a static completeness/link/fence check. At that time all eight phase guides were Not started. This historical result does not validate application or model behaviour; see the build log for its scope.

## Phase tracker

| Phase | Status | ADR | Handoff |
| --- | --- | --- | --- |
| 01 | In progress | [ADR 0001](adr/0001-foundation-config-logging.md) (Steps 2-6 only) | At phase completion |
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
- Settled in Step 2: Python 3.12 series and uv with one project lockfile; see ADR 0001. Dependency imports/install verified; application compatibility still requires later tests.
- Settled in Step 4: Pydantic Settings values precedence, accepted configuration modes, defaults, and inert AI/database connection settings; see ADR 0001. Settings construction tests pass.
- Settled in Step 5: minimal FastAPI application factory and process-only `/health` contract. No readiness dependencies are probed.
- Settled in Step 6: JSON log schema, duration in seconds, metadata allowlist, independent handlers, and correlation validation/context. Error HTTP responses are next.
- Exact tested Ollama image, model digest, hardware footprint, and latency: establish in Phase 06.
- AI quality criteria and observed judge agreement: establish in Phase 06/07; no accuracy claim yet.

The proposed business policy is in [requirements.md](requirements.md). Record any material change before implementing dependent work.

## Next chat

Continue Phase 01 with Step 7 only when requested. Read the guide, ADR 0001, and current Git state first. Phase completion records/handoff are still pending; Phase 02 has not started. Steps 2-5 are committed (Step 5: `5b8ed82`); Step 6 changes are uncommitted. The assistant has made no commits or pushes.
