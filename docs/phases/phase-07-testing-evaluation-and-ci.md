# Phase 07 - Core integration testing and CI

- Status: Not started.
- Milestone: Core validation.
- Prerequisite: prior phase outcomes inspected, including actual Phase 06 verification limits.
- Primary ADR to create: `docs/adr/0007-testing-evaluation-and-ci.md`.
- Handoff to create: `docs/handoffs/phase-07.md`.

## Objective

Consolidate evidence that the business workflow, polished UI, database, and core container work together. Add repeatable automated checks without requiring AI. Live AI evaluation and any LLM-judge calibration are deferred to final [Phase 09](phase-09-local-llm-integration.md).

## Read first

[AGENTS.md](../../AGENTS.md), [requirements](../requirements.md), [engineering guidelines](../python-engineering-guidelines.md), [AI usage](../ai-usage.md), current status, the Phase 06 handoff, relevant ADRs, and existing test results. Tests must already exist from earlier phases.

## Implementation tasks

- [ ] Map core acceptance scenarios to existing tests/manual evidence and fill meaningful gaps. Mark AI-specific AC-08/09 and the model portion of AC-10 as deferred to Phase 09 rather than passed.
- [ ] Consolidate permission, self-review, idempotency replay/conflict, revision fidelity, competing writes, atomic history, and persistence regression cases.
- [ ] Verify important UI interactions against the API contract, including reruns, retries, stale screens, and session-scoped AI choices.
- [ ] Add repeatable core-container startup, persistence, and cached-image restart scenarios using isolated synthetic storage; preserve existing volumes.
- [ ] Configure repository CI for install, lint/format checks, and ordinary automated tests. Keep routine checks independent of real model downloads, paid APIs, and private systems.
- [ ] Keep live-model evaluation and resource-heavy container checks separately invoked and accurately labelled. Do not publish results or change remote settings without authorisation.

## Verification and evidence

Run the actual core suite and inspect output. Record UI/API/database/container failures and coverage limits. No model download, live AI evaluation, or judge implementation belongs in this phase.

Report actual core evidence and missing coverage; distinguish assistant review from human acceptance. Expected artefacts may include core smoke scenarios and a CI workflow. AI evaluation fixtures, runner, and report belong to Phase 09 and are not assumed to exist now.

## Acceptance criteria

- [ ] Every critical business guarantee has inspected test/scenario evidence.
- [ ] Core tests and automated checks pass without a model or external network at test execution time.
- [ ] Container persistence, core-only startup, and the human workflow without AI are exercised.
- [ ] CI runs core checks without downloading models or requiring private systems.
- [ ] Reports contain actual observations and clearly defer AI quality/judge claims to Phase 09.

## Decision record and handover

Explain test-level choices, CI boundaries, core coverage and release-relevant gaps. Update this guide, the ADR index, [build log](../build-log.md), [AI usage](../ai-usage.md), and [project status](../project-status.md). Write a handoff that makes any incomplete core check or human-review requirement visible.

Stop after Phase 07. The next phase validates the handover and submission experience.
