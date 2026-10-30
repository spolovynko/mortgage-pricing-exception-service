# Phase 06 - UI redesign, database review, and reproducibility

- Status: Implemented and assistant-verified. The user considered Step 2 complete; formal Phase 06 acceptance is not recorded. See [verification](../build-log.md#2026-10-30---phase-06-ui-database-and-reproducibility).
- Milestone: MVP2 hardening.
- Prerequisite: Phase 05 implemented human UI/API and container workflow.
- Primary ADR to create: `docs/adr/0006-ui-and-database-hardening.md`.
- Handoff to create: `docs/handoffs/phase-06.md`.
- Optional LLM integration and AI evaluation are deferred to [Phase 09](phase-09-local-llm-integration.md).

## Objective

Solidify the existing human workflow through a substantial UI redesign, an evidence-backed database review, and a reproducible core setup. The user selected a substantial redesign rather than incremental visual polish. Preserve user data, exact reviewed versions, decision history, backend authority, and the single-process same-origin architecture. No AI implementation belongs in this phase.

## Read first

[AGENTS.md](../../AGENTS.md), current [project status](../project-status.md), the [Phase 05 handoff](../handoffs/phase-05.md), and affected UI/API/persistence code. Consult requirements, engineering guidelines, architecture, and ADRs only for concrete review questions.

## Agreed phase plan and closeout

Work one user-authorized step at a time. Report changes, checks and limits in chat, then wait for authorization before the next step. Reuse observed evidence; do not repeat checks unless code changes, failures or a concrete concern justify it. Model choices below are suggestions; the user controls selection.

| Step | Substeps | Why / result | Suggested model and effort |
| --- | --- | --- | --- |
| 1. Reconcile scope and evidence | Inspect Git, this guide, current status, the Phase 05 handoff, affected code and existing evidence. Identify what was implemented and what still lacks verification or a user decision; check the current UI preference without assuming a visual style was accepted. | Establish an accurate closeout scope without repeating completed work or claiming human acceptance. | GPT-6 Luna, medium |
| 2. Verify UI workflow | Check manager/reviewer switching, application prefill, draft preservation, create/retry, review, revision, history, stale/error handling and keyboard/responsive behavior. Run focused checks; fix observed defects within the authorized scope. Surface material visual redesign choices before implementing them. | Verify the submitted and reviewed terms remain accurate and the human workflow is usable. | GPT-6 Luna, medium; GPT-6.1 Terra, medium only for visual/browser diagnosis |
| 3. Verify database integrity | Inspect evidence for migration, nullable financial defaults, seed updates, immutable versions/decisions, permissions, idempotency, rollback and competing writes. Run affected checks where evidence is missing or changes warrant it; repair substantiated defects. | Establish safe persistence and preserve existing records; avoid speculative schema changes. | GPT-6 Luna, medium; GPT-6 Sol, medium for concurrency or migration issues |
| 4. Verify reproducibility | Follow only the README from an isolated source copy and uniquely named synthetic storage. Check build/start, migrations/seeds, create/decide/history, restart persistence, cached-image restart and isolated backup/restore. Preserve all volumes and user data; ask before host networking changes. | Demonstrate a reproducible core setup; distinguish same-host verification from a separate-machine test and record any limit. | GPT-6 Luna, medium; GPT-6 Sol, medium for container or networking diagnosis |
| 5. Gate and records | Run the required full suite once, plus Ruff, formatting, JavaScript syntax and Node tests, dependency/lock consistency, Compose and documentation validation, and relevant configuration/image checks. Fix failures and rerun only affected checks. Then update supported checkboxes, ADR 0006/index, build/AI logs, handoff, status and affected guidance. | Record exact evidence and remaining limits; stop at the Phase 06 boundary. | GPT-6 Luna, medium; GPT-6 Sol, medium for difficult failures |

Earlier focused checks, the isolated UI preview and the migration backup are not substitutes for the remaining reproducibility checks and final phase gate. The proposed visual options have not been recorded as selected or accepted.

## Tasks and acceptance

- [x] UI/database review findings and chosen scope are recorded without speculative refactors or invented bank policy.
- [x] UI changes preserve API contracts and pass affected checks plus live browser review of the human workflow.
- [x] Database integrity, version/decision preservation, concurrency, migrations, and seed behavior have inspected evidence; meaningful fixes have regression coverage.
- [x] Core setup succeeds from isolated source/storage without hidden local configuration, an LLM, a GPU, or paid/private services.
- [x] Restart persistence and isolated backup/restore preserve expected synthetic records; no existing data or volumes are removed.
- [x] Required full suite, static checks, dependency/lock consistency, Compose validation, documentation checks, and relevant container checks pass; failures and platform limits remain explicit.
- [x] Records distinguish assistant checks from human acceptance; no production-readiness or untested-machine claim is made.

## Reproducibility boundaries

Commit source, dependency lockfile, migrations, synthetic seed definitions, configuration examples, Dockerfile, Compose file, and setup instructions. Keep secrets, real databases, runtime volumes, and model weights out of Git. Core first setup needs access to image/package registries unless supplied with preloaded artefacts; offline restart is a separate check.

Future Phase 09 will define a pinned model/runtime manifest and automatic download/verification into persistent model storage. Any offline distribution would be a separate licensed bundle with checksums, not weights in source control.

## Evidence and handover

Follow repository phase-gate requirements. Store exact commands/results once in the build log and link from other records. Use `Implemented` only with code/check evidence and `Accepted` only with explicit human acceptance. No commit, push, or publication is authorised.
