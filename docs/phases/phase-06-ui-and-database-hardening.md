# Phase 06 - UI redesign, database review, and reproducibility

- Status: In progress; initial code/database review performed, application changes not started. The user selected a substantial UI redesign on 2026-10-30.
- Milestone: MVP2 hardening.
- Prerequisite: Phase 05 implemented human UI/API and container workflow.
- Primary ADR to create: `docs/adr/0006-ui-and-database-hardening.md`.
- Handoff to create: `docs/handoffs/phase-06.md`.
- Optional LLM integration and AI evaluation are deferred to [Phase 09](phase-09-local-llm-integration.md).

## Objective

Solidify the existing human workflow through a substantial UI redesign, an evidence-backed database review, and a reproducible core setup. The user selected a substantial redesign rather than incremental visual polish. Preserve user data, exact reviewed versions, decision history, backend authority, and the single-process same-origin architecture. No AI implementation belongs in this phase.

## Read first

[AGENTS.md](../../AGENTS.md), current [project status](../project-status.md), the [Phase 05 handoff](../handoffs/phase-05.md), and affected UI/API/persistence code. Consult requirements, engineering guidelines, architecture, and ADRs only for concrete review questions.

## Agreed phase plan

1. Review the current UI and database; report concrete usability/integrity findings and prioritise fixes before changing application behavior. Confirm the user's preferred extent of UI changes.
2. Redesign the workspace substantially: persistent navigation, a scan-friendly request queue, a dedicated request composer, a focused review/detail layout, and a readable version/decision timeline. Preserve unsent drafts across navigation/filter changes and keyboard focus across updates; provide clear labels, validation/errors, loading/empty states, responsive layout, and safe rendering. Keep identity, retries, exact-version review, and history usable; clearly label deferred AI without giving unavailable controls priority over the human workflow.
3. Address substantiated database findings: schema/foreign keys, immutable records, exact-version links, transaction/race boundaries, migration compatibility, and repeatable synthetic seeds. Add migrations only when necessary; never reset live storage.
4. Verify reproducibility from an isolated source copy and new named storage using README-only instructions: build/start, migrate/seed, create/revise/decide/history, restart persistence, and an isolated backup/restore exercise. Identify architecture/resource prerequisites and distinguish same-host verification from actual second-machine evidence.
5. Run the phase gate once and consolidate the ADR, handoff, guide, status, build/AI logs, and relevant runtime guidance. Stop before Phase 07.

## Tasks and acceptance

- [ ] UI/database review findings and chosen scope are recorded without speculative refactors or invented bank policy.
- [ ] UI changes preserve API contracts and pass affected checks plus live browser review of the human workflow.
- [ ] Database integrity, version/decision preservation, concurrency, migrations, and seed behavior have inspected evidence; meaningful fixes have regression coverage.
- [ ] Core setup succeeds from isolated source/storage without hidden local configuration, an LLM, a GPU, or paid/private services.
- [ ] Restart persistence and isolated backup/restore preserve expected synthetic records; no existing data or volumes are removed.
- [ ] Required full suite, static checks, dependency/lock consistency, Compose validation, documentation checks, and relevant container checks pass; failures and platform limits remain explicit.
- [ ] Records distinguish assistant checks from human acceptance; no production-readiness or untested-machine claim is made.

## Reproducibility boundaries

Commit source, dependency lockfile, migrations, synthetic seed definitions, configuration examples, Dockerfile, Compose file, and setup instructions. Keep secrets, real databases, runtime volumes, and model weights out of Git. Core first setup needs access to image/package registries unless supplied with preloaded artefacts; offline restart is a separate check.

Future Phase 09 will define a pinned model/runtime manifest and automatic download/verification into persistent model storage. Any offline distribution would be a separate licensed bundle with checksums, not weights in source control.

## Evidence and handover

Follow repository phase-gate requirements. Store exact commands/results once in the build log and link from other records. Use `Implemented` only with code/check evidence and `Accepted` only with explicit human acceptance. No commit, push, or publication is authorised.
