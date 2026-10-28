# Project status

Last updated: 2026-10-28

## Current position

- Repository state: documentation scaffold only.
- Scaffold placement: documents are present in the active Git working folder; the existing repository title and .gitignore were preserved. No implementation commit was created by the placement task.
- Current implementation phase: not started.
- Next phase: [Phase 01 - Foundation, configuration, logging](phases/phase-01-foundation-config-logging.md).
- Application/API/UI/Docker/model implementation: not present.
- Application test and live-model evaluation results: not available.
- Active work time: not recorded; do not infer it from conversation dates.

Documentation scaffold verification on 2026-10-28: 21 Markdown files and 105 relative links passed a static completeness/link/fence check. All eight phase guides remain Not started. This result does not validate application or model behaviour; see the build log for its scope.

## Phase tracker

| Phase | Status | ADR | Handoff |
| --- | --- | --- | --- |
| 01 | Not started | To be written | To be written |
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
- Dependency resolver/lock workflow and baseline Python version: settle in Phase 01.
- Exact tested Ollama image, model digest, hardware footprint, and latency: establish in Phase 06.
- AI quality criteria and observed judge agreement: establish in Phase 06/07; no accuracy claim yet.

The proposed business policy is in [requirements.md](requirements.md). Record any material change before implementing dependent work.

## Next chat

Implement Phase 01 using its guide and AGENTS.md. Creating this scaffold does not authorise implementing all phases in one chat.
