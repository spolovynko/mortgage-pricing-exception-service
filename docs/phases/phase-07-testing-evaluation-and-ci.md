# Phase 07 - Core integration testing and CI

- Status: Complete; assistant verification complete. Formal human acceptance is not recorded.
- Milestone: Core validation.
- Prerequisite: prior phase outcomes inspected, including actual Phase 06 verification limits.
- Primary ADR: [0007](../adr/0007-testing-evaluation-and-ci.md).
- Handoff: [Phase 07](../handoffs/phase-07.md).

## Objective

Consolidate evidence that the business workflow, polished UI, database, and core container work together. Add repeatable automated checks without requiring AI. Live AI evaluation and any LLM-judge calibration are deferred to final [Phase 09](phase-09-local-llm-integration.md).

## Read first

[AGENTS.md](../../AGENTS.md), [requirements](../requirements.md), [engineering guidelines](../python-engineering-guidelines.md), [AI usage](../ai-usage.md), current status, the Phase 06 handoff, relevant ADRs, and existing test results. Tests must already exist from earlier phases.

## Implementation tasks

- [x] Map core acceptance scenarios to existing tests/manual evidence. AI-specific AC-08/09 and the model portion of AC-10 remain deferred to Phase 09.
- [x] Inspect existing permission, self-review, idempotency, revision, competing-write, atomic-history and persistence regression coverage; add no duplicate backend tests.
- [x] Verify UI retry, stale-screen, API error, responsive width and keyboard focus behavior; correct application lookup fields in the Phase 03 API contract. There is no AI control in the current UI.
- [x] Add `scripts/core-container-smoke.ps1` for isolated synthetic startup, create, approve, history, persistence and cached-image recreation. The uniquely named volume is deliberately preserved after Compose cleanup.
- [x] Configure `.github/workflows/ci.yml` for locked install, Ruff, JavaScript syntax, Node UI tests and pytest; checks require no model or private service.
- [x] Keep the resource-heavy container smoke separate from ordinary CI. AI evaluation remains deferred.

## Verification and evidence

Run the actual core suite and inspect output. Record UI/API/database/container failures and coverage limits. No model download, live AI evaluation, or judge implementation belongs in this phase.

Report actual core evidence and missing coverage; distinguish assistant review from human acceptance. Expected artefacts may include core smoke scenarios and a CI workflow. AI evaluation fixtures, runner, and report belong to Phase 09 and are not assumed to exist now.

## Acceptance criteria

- [x] Every critical business guarantee has inspected test/scenario evidence.
- [x] Core tests and automated checks pass without a model or external network at test execution time (dependency installation used configured package access).
- [x] Container persistence, core-only startup, and the human workflow without AI are exercised.
- [x] CI runs core checks without downloading models or requiring private systems; hosted CI itself has not yet run.
- [x] Reports contain actual observations and clearly defer AI quality/judge claims to Phase 09.

## Decision record and handover

Explain test-level choices, CI boundaries, core coverage and release-relevant gaps. Update this guide, the ADR index, [build log](../build-log.md), [AI usage](../ai-usage.md), and [project status](../project-status.md). Write a handoff that makes any incomplete core check or human-review requirement visible.

Stop after Phase 07. The next phase validates the handover and submission experience.
