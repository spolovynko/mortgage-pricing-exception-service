# Project status

Last updated: 2026-10-31

## Current position

- Phases 01–08 are implemented with historical evidence in their handoffs. Phase 09 local AI, Docker preparation, advisory streaming, and release polish are implemented and assistant-verified; human semantic evaluation remains pending, so Phase 09 is **Incomplete — needs follow-up** rather than formally accepted.
- Reviewer installation requires Docker with Compose and a browser only; the AI profile pulls official Ollama and prepares the selected Qwen model automatically. Git, Python, uv, Node, and host Ollama are optional for this reviewer path.
- Current advisory contract: prompt v6, report schema v4, completeness rubric v2. AI advice is nonbinding and separate from exact-version human decisions. Model digest, submitted snapshot, contract/settings versions, and runtime endpoint define cache identity. Metrics are retained without logging prose payloads.
- Release controls and results: see the single [Phase 09 build entry](build-log.md#2026-10-31---phase-09-local-ai-and-release-polish), [ADR 0011](adr/0011-local-llm-integration.md), and [handoff](handoffs/phase-09.md). Tests, fresh Docker model preparation, network-isolated cached restart, and runtime-failure/manual-decision checks passed on this host.
- At the user's explicit request, the local demo database was backed up, erased, migrated and reseeded. It contains only fictional seed users/applications and no requests or decisions. Existing Docker volumes/caches were preserved; isolated release-test resources were removed. Local Uvicorn instances were stopped for the reset.
- Production deployment remains gated on real identity integration, approved bank policy, human AI evaluation, privacy/backup/audit controls, operational sign-off, and repository licensing; see [production requirements](production-notes.md). Header demo identities are not authentication.
- Git: working on `main`, base HEAD `0f709ea`; changes are uncommitted. No assistant commit, push, remote creation, or PR. The user approved the new report presentation; this does not constitute acceptance of golden labels or a production release.
- Next action: human review of candidate-v2 recommendations/explanations and resolution of production gates. No additional implementation phase is automatically started. Active work time and hosted CI execution are not recorded.

## Phase tracker

| Phase | Status | ADR | Handoff |
| --- | --- | --- | --- |
| 01 | Complete | [ADR 0001](adr/0001-foundation-config-logging.md), Implemented | [Phase 01](handoffs/phase-01.md) |
| 02 | Complete | [ADR 0002](adr/0002-database-and-seed-data.md), Implemented | [Phase 02](handoffs/phase-02.md) |
| 03 | Complete | [ADR 0003](adr/0003-business-rules-and-api.md), Implemented | [Phase 03](handoffs/phase-03.md) |
| 04 | Complete | [ADR 0004](adr/0004-user-interface.md), superseded by [ADR 0009](adr/0009-single-process-html-ui.md); [ADR 0010](adr/0010-versioned-request-context.md), Implemented | [Phase 04](handoffs/phase-04.md) |
| 05 | Complete | [ADR 0005](adr/0005-containerisation.md), Implemented | [Phase 05](handoffs/phase-05.md) |
| 06 — UI/database hardening | Complete (assistant-verified; acceptance not recorded) | [ADR 0006](adr/0006-ui-and-database-hardening.md) | [Phase 06](handoffs/phase-06.md) |
| 07 | Complete (assistant-verified; acceptance not recorded) | [ADR 0007](adr/0007-testing-evaluation-and-ci.md), Implemented | [Phase 07](handoffs/phase-07.md) |
| 08 | Complete (assistant-verified; acceptance not recorded) | [ADR 0008](adr/0008-documentation-and-handover.md), Implemented | [Phase 08](handoffs/phase-08.md) |
| 09 — Optional local AI/evaluation | Incomplete — needs human evaluation; technical checks passed | [ADR 0011](adr/0011-local-llm-integration.md), Implemented | [Phase 09](handoffs/phase-09.md) |

Allowed phase states: Not started, In progress, Complete, or Incomplete - needs follow-up. Describe any impediment in plain language. Completion must be backed by the guide's acceptance evidence.

## Agreed implementation direction

- Python API and static asset serving with FastAPI; HTML/CSS/JavaScript UI; SQLite through SQLAlchemy.
- Versioned database changes with Alembic.
- One application Dockerfile and one Compose file; one core application container runs one Uvicorn process serving both UI and API (user-authorized requirement change, 2026-10-29).
- Optional Ollama and model-initialisation services selected through an `ai` profile.
- Human approval in every operating mode. The UI toggle controls new AI assistance calls.
- Configuration and structured logging are implemented from Phase 01.
- Documentation and commit conventions apply across all phases.

## Remaining decisions and next action

Core API, transaction, versioning, UI, container, and optional AI design decisions are recorded in the ADR index. Review [candidate v2](../evals/phase09/golden-candidate-v2.json) and the [evaluation protocol](../evals/phase09/README.md) with an accountable human reviewer before claiming narrative accuracy or accepting those labels. Production requirements are listed separately and remain open. Historical setup incidents and verification limits remain in the prior build entries and handoffs; they have not been erased by this cleanup.
