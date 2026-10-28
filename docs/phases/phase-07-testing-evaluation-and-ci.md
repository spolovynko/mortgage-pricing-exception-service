# Phase 07 - Integration testing, AI evaluation, and CI

- Status: Not started.
- Milestone: MVP3.
- Prerequisite: prior phase outcomes inspected, including actual Phase 06 verification limits.
- Primary ADR to create: `docs/adr/0007-testing-evaluation-and-ci.md`.
- Handoff to create: `docs/handoffs/phase-07.md`.

## Objective

Consolidate evidence that the business workflow, UI, containers, and optional AI work together. Add repeatable automated checks and calibrate any LLM judge against independently labelled cases.

## Read first

[AGENTS.md](../../AGENTS.md), [requirements](../requirements.md), [engineering guidelines](../python-engineering-guidelines.md), [AI usage](../ai-usage.md), current status, the Phase 06 handoff, relevant ADRs, and existing test results. Tests must already exist from earlier phases.

## Implementation tasks

- [ ] Map acceptance scenarios AC-01 through AC-10 to existing tests/manual evidence and fill meaningful gaps.
- [ ] Consolidate permission, self-review, idempotency replay/conflict, revision fidelity, competing writes, atomic history, and persistence regression cases.
- [ ] Verify important UI interactions against the API contract, including reruns, retries, stale screens, and session-scoped AI choices.
- [ ] Add repeatable core-container smoke scenarios and first-download/cached-restart checks using disposable test storage.
- [ ] Create a versioned synthetic evaluation set covering faithful summaries, invented facts, omissions, ambiguous claims, adversarial text, and generation failures.
- [ ] Obtain actual human labels/review for the reference cases. Agent-generated labels remain provisional until a human has checked them; record that status accurately.
- [ ] Define a rubric before comparing outputs: faithfulness, unsupported claims, preservation of discount/application identity, useful missing-information findings, and evidence limits.
- [ ] Implement an explicit live evaluation runner, with machine-readable results and a concise report. Record the exact model/runtime/prompts/settings/hardware used.
- [ ] Add an optional LLM-judge path that grades generated summaries against source input and the rubric. Compare judge outcomes with human labels and report false passes and disagreements.
- [ ] Measure repeated-run consistency and latency. Do not treat self-agreement or a small sample as production validation.
- [ ] Configure repository CI for install, lint/format checks, and ordinary automated tests. Keep routine checks independent of real model downloads, paid APIs, and private systems.
- [ ] Keep live-model evaluation and resource-heavy container checks separately invoked and accurately labelled. Do not publish results or change remote settings without authorisation.

## Verification and evidence

Run the actual core suite and inspect output. Run the real-model evaluations if the environment supports them; capture failures rather than silently replacing them with fake output. A fixed rubric can produce pass/fail labels and error counts; choose thresholds consciously in the ADR instead of inventing favourable targets after seeing results.

Report dataset size, human-review status, missing test coverage, judge disagreement/false-pass counts, and latency statistics where measured. Keep model-generation defects distinct from judge defects. A judge that is not accurate enough can be reported as an experimental bonus; it cannot become the approval gate.

Expected new artefacts may include evaluation fixtures, scripts/evaluate_ai.py, docs/evaluation-report.md, and a CI workflow. They are created in this phase, not assumed to exist now.

## Acceptance criteria

- [ ] Every critical business guarantee has inspected test/scenario evidence.
- [ ] Core tests and automated checks pass without a model or external network at test execution time.
- [ ] Container persistence, core-only startup, and AI-unavailable operation are exercised.
- [ ] AI quality results identify their actual dataset, human-label status, runtime, settings, and limitations.
- [ ] Any LLM-judge claim is supported by comparison with actual human labels; missing calibration is explicitly reported and its criterion remains incomplete.
- [ ] The evaluation report contains actual results, not example scores presented as observations.

## Decision record and handover

Explain test-level choices, CI boundaries, rubric/threshold choices, judge calibration, and release-relevant gaps. Update this guide, the ADR index, [build log](../build-log.md), [AI usage](../ai-usage.md), and [project status](../project-status.md). Write a handoff that makes any incomplete evaluation or human-review requirement visible.

Stop after Phase 07. The next phase validates the handover and submission experience.
