# Implementation plan

Status: Phases 01–05 are implemented and assistant-verified; human acceptance is not recorded. Phase 06 now focuses on UI/database hardening and reproducibility. Optional local AI is deferred to the final Phase 09 by the user on 2026-10-30. See [project status](project-status.md).

This plan implements the requirements and the user's agreed additions: a same-origin HTML/CSS/JavaScript UI, optional local AI, automatic model setup, operational logging, central configuration, and one application Dockerfile with one Compose file.

## Phase sequence

| Phase | Guide | Milestone | Completion outcome |
| --- | --- | --- | --- |
| 01 | [Foundation, configuration, logging](phases/phase-01-foundation-config-logging.md) | MVP1 | Testable project skeleton, validated settings, structured logs |
| 02 | [Database and seed data](phases/phase-02-database-and-seed-data.md) | MVP1 | Migrated persistent storage, repeatable seed data, integrity constraints |
| 03 | [Business rules and API](phases/phase-03-business-rules-and-api.md) | MVP1 | Complete tested human approval workflow through HTTP |
| 04 | [User interface](phases/phase-04-user-interface.md) | MVP2 | Request, review, revision, history, and AI-control screens |
| 05 | [Containerisation](phases/phase-05-containerisation.md) | MVP2 | Core UI/API startup through one Compose command |
| 06 | [UI and database hardening](phases/phase-06-ui-and-database-hardening.md) | MVP2 hardening | Polished human workflow, reviewed database integrity, reproducible core setup |
| 07 | [Integration testing and CI](phases/phase-07-testing-evaluation-and-ci.md) | Core validation | Integrated business/UI/container evidence and automated checks without a model |
| 08 | [Documentation and handover](phases/phase-08-documentation-and-handover.md) | Core handover | Verified fresh setup, demonstration, honest limitations and submission record |
| 09 | [Optional local LLM integration and AI evaluation](phases/phase-09-local-llm-integration.md) | Optional MVP3 | Cached model setup, advisory assessments, live evaluation and any judge calibration |

Phases are sequential for this project. A phase can prepare an interface for a later feature, but it must identify unavailable functionality clearly. Tests, logging, ADRs, build records, AI-use notes, and documentation are maintained throughout; they are not deferred to Phase 07 or 08.

## Delivery milestones

- **MVP1:** API-level create, inspect, revise, decide, history, and approved-discount retrieval work with seed data. Critical permission, retry, and competing-update cases are tested.
- **MVP2:** A reviewer can use the complete human workflow through the containerised UI. One application container runs one Uvicorn process serving both UI and API, per the user's 2026-10-29 requirement change. Application data survives restarts.
- **MVP3 (optional, Phase 09):** Optional local AI is automatically prepared and evaluated. Human approval works with assistance on, off, or unavailable. The final documentation and reproducibility checks are complete.

MVP2 and MVP3 are delivery labels for this exercise, not claims of production maturity. The PDF treats a custom UI and an additional AI demonstration as bonuses; the UI is implemented and the additional live AI demonstration is deferred to the final optional phase.

## One chat per phase

Start in this repository and ask the agent to implement a specific guide. Reuse an agreed plan and selected model; otherwise establish a short phase plan. Read current status, the active guide, previous handoff, and only supporting sections needed for concrete questions. Follow the strict economy defaults in [AGENTS.md](../AGENTS.md): targeted reads, focused checks, brief replies, and consolidated phase-completion records.

The authoritative current position is [project-status.md](project-status.md). The build log records chronology; ADRs preserve reasoning; handoffs provide concise continuation context. If code and documentation disagree, inspect the evidence and repair the documentation or implementation explicitly.

## Phase completion gate

Each phase requires implemented outcomes, appropriate passing checks, recorded limitations, an ADR, and a handoff. Record incomplete work rather than checking off a planned feature. Do not advance automatically after finishing a phase.

## Scope control

Prioritise a complete, understandable workflow. Add no cloud dependency, credit-scoring model, mandatory GPU, distributed queue, vector database, or multi-agent runtime without an observed need and an explicit scope decision. Document production follow-ups rather than expanding the exercise indefinitely.
