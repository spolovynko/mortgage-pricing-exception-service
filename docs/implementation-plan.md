# Implementation plan

Status: Phase 01 complete. Phase 02 Steps 1-10 are complete; repeatable synthetic seed data is verified and database readiness is next. See [project status](project-status.md).

This plan implements the requirements and the user's agreed additions: a Python UI, optional local AI, automatic model setup, operational logging, central configuration, and one application Dockerfile with one Compose file.

## Phase sequence

| Phase | Guide | Milestone | Completion outcome |
| --- | --- | --- | --- |
| 01 | [Foundation, configuration, logging](phases/phase-01-foundation-config-logging.md) | MVP1 | Testable project skeleton, validated settings, structured logs |
| 02 | [Database and seed data](phases/phase-02-database-and-seed-data.md) | MVP1 | Migrated persistent storage, repeatable seed data, integrity constraints |
| 03 | [Business rules and API](phases/phase-03-business-rules-and-api.md) | MVP1 | Complete tested human approval workflow through HTTP |
| 04 | [User interface](phases/phase-04-user-interface.md) | MVP2 | Request, review, revision, history, and AI-control screens |
| 05 | [Containerisation](phases/phase-05-containerisation.md) | MVP2 | Core UI/API startup through one Compose command |
| 06 | [Local LLM integration](phases/phase-06-local-llm-integration.md) | MVP3 | Optional real model, cached automatic setup, advisory assessments |
| 07 | [Testing, evaluation, CI](phases/phase-07-testing-evaluation-and-ci.md) | MVP3 | Integrated evidence, AI evaluation and judge calibration, automated checks |
| 08 | [Documentation and handover](phases/phase-08-documentation-and-handover.md) | MVP3 | Verified fresh setup, demonstration, honest limitations and submission record |

Phases are sequential for this project. A phase can prepare an interface for a later feature, but it must identify unavailable functionality clearly. Tests, logging, ADRs, build records, AI-use notes, and documentation are maintained throughout; they are not deferred to Phase 07 or 08.

## Delivery milestones

- **MVP1:** API-level create, inspect, revise, decide, history, and approved-discount retrieval work with seed data. Critical permission, retry, and competing-update cases are tested.
- **MVP2:** A reviewer can use the complete human workflow through the containerised UI. One shared image supplies the API and UI containers. Application data survives restarts.
- **MVP3:** Optional local AI is automatically prepared and evaluated. Human approval works with assistance on, off, or unavailable. The final documentation and reproducibility checks are complete.

MVP2 and MVP3 are delivery labels for this exercise, not claims of production maturity. The PDF treats a custom UI and an additional AI demonstration as bonuses; both are included in this project's agreed plan.

## One chat per phase

Start in this repository and ask the agent to implement a specific guide. The agent first proposes a short step/substep plan and a cost/performance model recommendation, then proceeds with the requested phase. It reads the current status, guide, previous handoff, and only relevant supporting sections. It performs the work and checks, then writes concise phase records as directed by AGENTS.md.

The authoritative current position is [project-status.md](project-status.md). The build log records chronology; ADRs preserve reasoning; handoffs provide concise continuation context. If code and documentation disagree, inspect the evidence and repair the documentation or implementation explicitly.

## Phase completion gate

Each phase requires implemented outcomes, appropriate passing checks, recorded limitations, an ADR, and a handoff. Record incomplete work rather than checking off a planned feature. Do not advance automatically after finishing a phase.

## Scope control

Prioritise a complete, understandable workflow. Add no cloud dependency, credit-scoring model, mandatory GPU, distributed queue, vector database, or multi-agent runtime without an observed need and an explicit scope decision. Document production follow-ups rather than expanding the exercise indefinitely.
