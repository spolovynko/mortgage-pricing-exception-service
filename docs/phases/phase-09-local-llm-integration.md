# Phase 09 - Optional local LLM integration and AI evaluation

- Status: Incomplete — technical implementation and assistant verification complete; human semantic evaluation pending.
- Milestone: MVP3.
- Prerequisite: Phases 06-08 core hardening, testing, and handover outcomes inspected.
- Primary ADR: [0011](../adr/0011-local-llm-integration.md), Implemented.
- Handoff: [Phase 09](../handoffs/phase-09.md).
- Scheduling: optional Phase 09 was subsequently authorized and implemented; the current task consolidated release evidence on 2026-10-31.

## Objective

Add a narrowly defined, real local AI assistant and automatic model setup. Preserve complete human review when assistance is off, downloading, unavailable, or failing. LLM use is optional for reviewers: the default/core setup requires no Ollama installation, model download, GPU, or AI profile. Reviewers who cannot or do not want to install the optional runtime can skip AI and complete the human workflow. Ordinary setup and checks must not pull a model or require network access for inference.

## Read first

[AGENTS.md](../../AGENTS.md), [requirements](../requirements.md), [architecture](../architecture.md), [engineering guidelines](../python-engineering-guidelines.md), [AI usage](../ai-usage.md), current status, the Phase 05 handoff, and version/container ADRs.

## AI task and boundaries

The live assistant streams a concise advisory opinion about whether the submitted business rationale supports the specific requested concession. Completeness is a prerequisite for an approve suggestion, not sufficient justification. Vague reasons, missing evidence, and a reduction not explained by the reported offer call for further justification. These are exercise advisory safeguards, not bank pricing policy. The model never records a decision, changes status, grants a discount, or verifies outside evidence.

An optional LLM judge is not implemented. Human semantic review remains pending; machine label agreement is not a calibrated reasoning-accuracy measure or approval authority.

### Assessment contract

The user requested a readable advisory opinion with aggregated reasons on 2026-10-31, replacing the field-selection report. Prompt `pricing-exception-advisor-v6` and schema `assessment-report-v4` return `recommendation` (`approve`, `do_not_approve`, or `needs_more_information`), one concise `explanation`, practical `next_steps`, and `source_refs`. These are reviewable reasons, not private chain-of-thought or approval probabilities.

Capture the exact submitted version and supply a deterministic completeness checklist and exact rate arithmetic. Completeness alone does not justify approval. Restrict the generation schema to non-approve outcomes when required information is missing or the reported competing rate does not explain the full requested reduction. The latter is an exercise advisory constraint, not bank policy; human reviewers retain their normal decision authority. Vague retention claims warrant further commercial justification.

Validate output shape, evidence paths, supplied numeric facts, and selected unsupported policy assertions. Known internal field labels are rendered in plain English. Allow one bounded repair of rejected output, then fail visibly. These checks cannot establish semantic truth, claim authenticity, policy compliance, or prediction accuracy. Stream draft explanation text, persist only a validated final result, and retain audit metadata in a collapsed UI section. Suggestions never update decisions.

AI remains explicitly invoked and optional. Core submission, review, and human decisions work without a model. The active synthetic evaluation is [candidate v2](../../evals/phase09/golden-candidate-v2.json); labels and narrative quality require actual human review. Earlier field-selection/completeness scores do not measure this advisory task. See [ADR 0011](../adr/0011-local-llm-integration.md).

## Implementation tasks and evidence

- [x] Structured, evidence-linked advisory output, deterministic rate arithmetic, generation constraints, bounded concurrency/deadline, and one repair of invalid output.
- [x] Explicit assessment creation/stream/history routes, reviewer/ownership checks, exact submitted snapshots, stale-result handling, and separate persistence.
- [x] Model digest, prompt/rubric/schema/settings, metrics, and content-based cache identity; atomic replay under competing saves.
- [x] Optional session controls, readable draft streaming, validated final report, safe rendering, and human-only decision buttons.
- [x] One application image/process, official pinned Ollama image, AI-profile setup job, visible first-download progress, inference readiness, and cache reuse.
- [x] Core startup/readiness independent of the model; off/unavailable paths preserve the human workflow.
- [x] Secure bare-image defaults, explicit Compose demo identity/seeding, internal model addressing, read-only app filesystem, dropped capabilities, bounded safe logs, and no unnecessary model port.

## Acceptance criteria

- [x] The selected real local model returns a validated advisory report through the API; the UI renderer was visually checked with synthetic model output.
- [x] AI-off mode makes no runtime calls in ordinary tests; a stopped Docker model returns a safe failure while manual decisions and saved history remain usable.
- [x] Fresh isolated Docker startup automatically downloaded the model, printed progress, and exited model-init successfully after readiness inference.
- [x] Cached restart succeeded with image pulls disabled on an internal Docker network without external egress; this is not a claim of an offline first build.
- [x] Exact-version history, digest-aware replay, numeric/source checks, and in-flight staleness are covered by checks.
- [x] Runtime/model/license/hardware and live-test limits are recorded in the [build entry](../build-log.md#2026-10-31---phase-09-local-ai-and-release-polish).

## AI evaluation

- [x] Versioned synthetic candidate datasets and explicit rubric; candidate v2 evaluates advisory recommendations and reasoning. Ordinary tests remain model/network independent.
- [x] Explicit live runner and local report include model digest/runtime, contract/settings, hardware, latency, recommendation consistency, exact wording repeatability, failures, and limits.
- [ ] Obtain actual human labels and review rationale faithfulness/usefulness. Assistant-generated labels remain provisional; agreement is not independently established accuracy.
- [ ] Optional LLM judge: omitted. No judge calibration or legal-compliance claim is made.
- [x] README, installation, LLM use, troubleshooting, production requirements, ADR, logs, status, and handoff reflect implemented behavior.

Exact commands, outcomes, material failures, and limits are consolidated once in the [build log](../build-log.md#2026-10-31---phase-09-local-ai-and-release-polish). No core database or model is reset during ordinary startup.

## Decision record and handover

The selected model was retained as directed by the user; no repeated model comparison was performed. [ADR 0011](../adr/0011-local-llm-integration.md), [AI-use record](../ai-usage.md), [status](../project-status.md), and [handoff](../handoffs/phase-09.md) link to consolidated verification and remaining human/production gates.

Stop after Phase 09. If hardware/download access prevents live verification, record the implemented subset and unmet criteria rather than claiming a complete live integration.
