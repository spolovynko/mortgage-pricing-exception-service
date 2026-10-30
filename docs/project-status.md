# Project status

Last updated: 2026-10-30

## Current position

- Repository state: Phases 01–07 are implemented. Phase 07 is assistant-verified; formal human acceptance is not recorded. MVP2's containerised human UI/API workflow is implemented.
- Scaffold placement: documents are present in the active Git working folder; the existing repository title and .gitignore were preserved. No implementation commit was created by the placement task.
- Completed implementation phase: [Phase 01 - Foundation, configuration, logging](phases/phase-01-foundation-config-logging.md), implemented in user-requested Steps 1-8. See [handoff](handoffs/phase-01.md).
- Completed implementation phase: [Phase 02 - Database and seed data](phases/phase-02-database-and-seed-data.md). See [handoff](handoffs/phase-02.md).
- Completed implementation phase: [Phase 03 - Business rules and API](phases/phase-03-business-rules-and-api.md). See [handoff](handoffs/phase-03.md) and [ADR 0003](adr/0003-business-rules-and-api.md).
- Completed implementation phase: [Phase 04 - User interface](phases/phase-04-user-interface.md). Its original Streamlit runtime was replaced by the single-process HTML UI in [ADR 0009](adr/0009-single-process-html-ui.md); structured per-version request context is recorded in [ADR 0010](adr/0010-versioned-request-context.md). See [handoff](handoffs/phase-04.md), [architecture-update evidence](build-log.md#2026-10-29---phase-04-single-process-html-ui-update), and [context-extension evidence](build-log.md#2026-10-29---phase-04-structured-request-context).
- Completed implementation phase: [Phase 05 - Containerisation](phases/phase-05-containerisation.md). One non-root application container runs one Uvicorn process serving same-origin UI/API with persistent SQLite storage; see [ADR 0005](adr/0005-containerisation.md), [handoff](handoffs/phase-05.md), and [build evidence](build-log.md#2026-10-29---phase-05-containerisation).
- Completed implementation phase: [Phase 06 - UI/database hardening and reproducibility](phases/phase-06-ui-and-database-hardening.md); see [handoff](handoffs/phase-06.md) and [ADR 0006](adr/0006-ui-and-database-hardening.md). Formal phase acceptance is not recorded.
- Phase 07: implemented and assistant-verified; human acceptance and hosted CI execution are not recorded. See [guide](phases/phase-07-testing-evaluation-and-ci.md), [ADR 0007](adr/0007-testing-evaluation-and-ci.md), [handoff](handoffs/phase-07.md), and [build evidence](build-log.md#2026-10-30---phase-07-core-integration-testing-and-ci). AI evaluation remains deferred to Phase 09.
- Next action: begin Phase 08 documentation and handover.
- Project setup: Python 3.12 series, uv 0.11.6, `pyproject.toml` + `uv.lock`, `src/mortgage_pricing/__init__.py`, and ignored `.venv`. Fresh installation, isolated imports, lock consistency, and dependency consistency passed on Windows/CPython 3.12.12.
- Development checks: the original Streamlit Phase 04 suite passed 146 tests; the single-process HTML update passed 134 tests; its structured-context extension passed the final 138-test suite. Exact commands and scope limits are in the two linked Phase 04 build entries. Windows/CPython 3.12.12 only.
- Configuration: immutable Pydantic Settings and `.env.example` with validated modes, URLs, bounds, and documented precedence; configuration tests pass. It does not connect to a database or model.
- Persistence foundation: SQLAlchemy 2.0.55, Alembic 1.20.1, shared metadata, lazy engine/session factories, and user/application/request/version/decision/history/idempotency models. Step 3 configures SQLite transactions and foreign keys; Steps 4-7 add core models; Step 8 adds atomic create/revise/decide functions; Step 9 adds Alembic revision `20261029_0001`; Step 10 adds repeatable fictional users/applications; Step 11 adds database readiness. Follow-up revision `20261029_0002` adds nullable versioned context. See [ADR 0002](adr/0002-database-and-seed-data.md) and [ADR 0010](adr/0010-versioned-request-context.md).
- API: create/list/details/history, revisions, exact-version decisions, approved-pricing retrieval, and demo lookups are implemented alongside `/health` and `/ready`. See the [HTTP contract](phase-03-api-contract.md). Configured demo identity, permissions, exact-input creation replay, current-only pricing, and competing writes have observed test evidence; approval and decline also passed actual TCP HTTP scenarios. Final suite/static/dependency results are in the [Phase 03 build entry](build-log.md#2026-10-29---phase-03-business-rules-api-and-final-acceptance).
- Logging/errors: per-app JSON logger, ASGI tracing, safe diagnostics, and centralized error envelope/handlers. Live 200/404 checks passed from the fresh environment; Step 7 live 500 verification also passed. Unexpected exceptions before response start return a generic correlated 500. Failures after response start are logged/rethrown.
- UI: FastAPI serves `ui/index.html`, `ui/styles.css`, `ui/app.js`, and `ui/workspace.js` with same-origin API requests from one Uvicorn process. Root `ui/` is excluded from the Python wheel and copied into the application image. Demo identity is not production authentication. Phase 06 UI verification and its limits are recorded in the handoff.
- Containers: digest-pinned Python 3.12.12 image, locked non-editable installation, safe migration/seed entrypoint, one Compose service, UID/GID 10001, read-only root filesystem, named writable data volume, loopback port, database healthcheck, and bounded local logs are implemented. Docker Desktop 29.9.2 / Compose 5.6.1 live workflows verified create/approve/retrieve, recreation persistence, repeatable seeds, unavailable API recovery, and unwritable/read-only failures on Windows/WSL2.
- Active work time: not recorded; do not infer it from conversation dates.

Documentation scaffold verification on 2026-10-28: 21 Markdown files and 105 relative links passed a static completeness/link/fence check. At that time all eight phase guides were Not started. This historical result does not validate application or model behaviour; see the build log for its scope.

## Phase tracker

| Phase | Status | ADR | Handoff |
| --- | --- | --- | --- |
| 01 | Complete | [ADR 0001](adr/0001-foundation-config-logging.md), Implemented | [Phase 01](handoffs/phase-01.md) |
| 02 | Complete | [ADR 0002](adr/0002-database-and-seed-data.md), Implemented | [Phase 02](handoffs/phase-02.md) |
| 03 | Complete | [ADR 0003](adr/0003-business-rules-and-api.md), Implemented | [Phase 03](handoffs/phase-03.md) |
| 04 | Complete | [ADR 0004](adr/0004-user-interface.md), superseded by [ADR 0009](adr/0009-single-process-html-ui.md); [ADR 0010](adr/0010-versioned-request-context.md), Implemented | [Phase 04](handoffs/phase-04.md) |
| 05 | Complete | [ADR 0005](adr/0005-containerisation.md), Implemented | [Phase 05](handoffs/phase-05.md) |
| 06 — UI/database hardening | In progress | To be written | To be written |
| 07 | Complete (assistant-verified; acceptance not recorded) | [ADR 0007](adr/0007-testing-evaluation-and-ci.md), Implemented | [Phase 07](handoffs/phase-07.md) |
| 08 | Not started | To be written | To be written |
| 09 — Optional local AI/evaluation (deferred) | Not started | To be written | To be written |

Allowed phase states: Not started, In progress, Complete, or Incomplete - needs follow-up. Describe any impediment in plain language. Completion must be backed by the guide's acceptance evidence.

## Agreed implementation direction

- Python API and static asset serving with FastAPI; HTML/CSS/JavaScript UI; SQLite through SQLAlchemy.
- Versioned database changes with Alembic.
- One application Dockerfile and one Compose file; one core application container runs one Uvicorn process serving both UI and API (user-authorized requirement change, 2026-10-29).
- Optional Ollama and model-initialisation services selected through an `ai` profile.
- Human approval in every operating mode. The UI toggle controls new AI assistance calls.
- Configuration and structured logging are implemented from Phase 01.
- Documentation and commit conventions apply across all phases.

## Decisions still needing implementation detail

- API contracts, validation/storage limits, read permissions, creation replay semantics, and HTTP business/conflict/storage outcomes: implemented in [ADR 0003](adr/0003-business-rules-and-api.md). SQLite contention has bounded waits and no automatic retry.
- Settled in Step 2: Python 3.12 series and uv with one project lockfile; see ADR 0001. Final fresh-environment installation and foundation tests pass.
- Settled in Step 4: Pydantic Settings values precedence, accepted configuration modes, defaults, and inert AI/database connection settings; see ADR 0001. Settings construction tests pass.
- Settled in Phase 01 Step 5: minimal FastAPI application factory and process-only `/health` contract. Phase 02 added schema readiness; Phase 05 now also verifies writable SQLite storage through `/ready`.
- Settled in Step 6: JSON log schema, duration in seconds, metadata allowlist, independent handlers, and correlation validation/context.
- Settled in Step 7: safe HTTP/validation error envelope and request-boundary handling of unexpected failures, preserving correlation and standard HTTP headers.
- Settled in Step 8: optional UI stub omitted; application settings/tests are isolated from real shell/dotenv state. No foundation acceptance criteria remain unmet on the tested platform.
- Exact tested Ollama image, model digest, hardware footprint, and latency: deferred to Phase 09.
- AI quality criteria and any observed judge agreement: deferred to Phase 09; no accuracy claim yet.

The proposed business policy is in [requirements.md](requirements.md). Record any material change before implementing dependent work.

## Next chat

Begin Phase 07 when authorized, using the Phase 06 handoff; do not assume formal phase acceptance. Phases 07 and 08 cover core validation/CI and handover; Phase 09 contains deferred optional AI and evaluation. Core startup stays independent of model setup. Active work time is not recorded. No assistant commit or push.
