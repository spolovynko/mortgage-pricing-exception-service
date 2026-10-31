# Phase 09 - Optional local LLM integration and AI evaluation

- Status: Not started.
- Milestone: MVP3.
- Prerequisite: Phases 06-08 core hardening, testing, and handover outcomes inspected.
- Primary ADR to create: `docs/adr/0011-local-llm-integration.md` (0009 and 0010 already exist).
- Handoff to create: `docs/handoffs/phase-09.md`.
- Scheduling: deferred to the final optional phase by the user on 2026-10-30; no integration work has started.

## Objective

Add a narrowly defined, real local AI assistant and automatic model setup. Preserve complete human review when assistance is off, downloading, unavailable, or failing. LLM use is optional for reviewers: the default/core setup requires no Ollama installation, model download, GPU, or AI profile. Reviewers who cannot or do not want to install the optional runtime can skip AI and complete the human workflow. Ordinary setup and checks must not pull a model or require network access for inference.

## Read first

[AGENTS.md](../../AGENTS.md), [requirements](../requirements.md), [architecture](../architecture.md), [engineering guidelines](../python-engineering-guidelines.md), [AI usage](../ai-usage.md), current status, the Phase 05 handoff, and version/container ADRs.

## AI task and boundaries

The live assistant streams a report about the exact submitted version, flags checklist gaps, and provides a nonbinding suggested outcome for the human reviewer. The suggestion is based only on checklist completeness: suggest approve when no material checklist items are missing; suggest do not approve when material information is missing. This is an exercise signal, not lending policy. It never records a decision, changes status, grants a discount, or verifies outside evidence.

An LLM judge that grades summaries is a separate evaluation component, deferred here from Phase 07. It can be evaluated only after live assessment generation exists. Do not conflate that score with approval authority.

### Assessment contract (prompt/checklist v1)

The versioned checklist is `pricing-exception-review-v1`; the system prompt is `pricing-exception-advisor-v2`. Input is a server-captured snapshot of one exact request version: request and application identifiers, version number, requested discount, submission reason, and the version's structured application/context fields. Treat all user-provided text as untrusted data, never as instructions. Do not send decision history or unrelated requests. Cap the serialized input at 12,000 UTF-8 bytes; reject oversize input with a clear validation error rather than silently omitting fields.

The model returns a strict JSON object with summary, reported claims, missing information, and limitations. The backend adds `suggested_outcome` (`suggest_approve` or `suggest_do_not_approve`) and `outcome_rationale` (at most 500 characters) deterministically from the structured exercise checklist fields; model prose cannot set this signal. Cap the raw model response at 8,000 UTF-8 bytes and validate every field before storage or display. Stream generated JSON fragments to the reviewer, then replace them with the validated formatted report. Persist only a fully validated result. Source references point only to submitted snapshot fields; they do not establish that a claim is true. State explicitly that manager-reported claims are unverified and external evidence is not checked.

Checklist v1 asks whether the submitted snapshot identifies the application and requested terms; states the request reason; supplies the context exercise fields needed to understand that reason; includes a competitor rate and expiry only when a competitor offer is claimed; and clearly separates reported assertions from verified information. This is an exercise completeness checklist, not lending policy. The output is advisory; a reviewer must inspect the submitted version and make the decision independently.

Reviewer path: follow the normal core setup and use the service without AI. Starting the app with default settings must not start Ollama or download a model. AI appears only when explicitly enabled and generated; if the optional runtime is absent or fails, explain that assistance is unavailable and leave submission, review, and decisions usable. Suggestions never update request state; a reviewer records every decision.

## Implementation tasks

- [x] Define checklist `pricing-exception-review-v1`, prompt `pricing-exception-advisor-v2`, streamed report schema, bounded input/output, and checklist-only suggested outcomes. See Assessment contract above.
- [ ] Implement a small Ollama adapter with explicit timeout, limited retries, bounded concurrency, and schema/error handling.
- [ ] Add assessment creation/status endpoints and enforce identity/version requirements on the server.
- [ ] Capture version input before inference, avoid holding a database write transaction during inference, and handle a revision/decision occurring while generation is running.
- [ ] Store assessment separately from decisions, with exact request version, model identity/digest, prompt/checklist version, timing, and result state. Old results cannot be presented as current advice.
- [ ] Connect the session toggle and Generate button. Off prevents new calls; existing records remain. Changing the toggle does not control Docker or automatically trigger a call.
- [ ] Implement truthful AI availability states and useful errors. Keep the human workflow and core readiness independent.
- [ ] Add Ollama and model-init services under the ai Compose profile, reusing the existing application Dockerfile/image for the Python setup job.
- [x] Use pinned Ollama image `ollama/ollama:0.40.13@sha256:93c1376d651a9f1579ee40cc5763852f08b204466371e4bb64bca2a1d8d08e2d` (linux/amd64) and persistent `model-cache` volume. The user selected `qwen3:4b-instruct-2507-q4_K_M`; registry reports digest `0edcdef34593`, 2.5 GB, and Apache-2.0. Runtime/model live behavior and hardware performance remain unverified.
- [ ] In model-init, wait for runtime readiness, inspect the local cache, download only when missing with visible progress, verify the selected model, and perform a small inference readiness check.
- [ ] Use bounded retries with a clear failure result. No permanent startup loop or false ready state.
- [ ] Disable Ollama cloud features for the local-only mode. Publish no unnecessary model port. Never commit weights or bake them into the application image.

## Verification

First run ordinary adapter/API/UI tests with explicit fakes: disabled AI makes no call; timeout, malformed/truncated response, unavailable runtime, stale assessment, and misleading instructions in input are handled safely. Confirm the model cannot alter an approval record.

Then exercise the actual selected model on the actual tested hardware. Record model digest/quantisation, runtime image, settings, context/output limits, hardware, latency, and memory observations. A 16 GB host is a planning recommendation, not a tested minimum or performance promise.

Verify first-run download and cache reuse using isolated test volumes:

```bash
$env:LLM_MODE = 'auto'
$env:LLM_BASE_URL = 'http://ollama:11434'
$env:LLM_MODEL = 'qwen3:4b-instruct-2507-q4_K_M'
docker compose --profile ai up --build
```

After initial setup, verify an existing-image restart with external internet disconnected:

```bash
docker compose --profile ai up
```

Do not force registry updates or downloads when the required cached artefact is already present. Test model failure while the core application remains usable.

## Acceptance criteria

- [ ] The real local model produces a validated advisory assessment through the UI/API.
- [ ] Core mode and assistance-off mode make no inference calls and allow human decisions.
- [ ] First AI startup downloads automatically, reports progress, caches persistently, and distinguishes failure from readiness.
- [ ] A subsequent cached restart works offline on the tested environment.
- [ ] Assessment/version metadata and model failures are handled correctly without partial approvals.
- [ ] Runtime, licence, model, hardware, and live-test evidence are recorded honestly. Untested items remain unchecked.

## Deferred AI evaluation

- [ ] Define a versioned synthetic evaluation set and rubric before measuring live output: faithfulness, unsupported claims, exact request/discount identity, useful checklist findings, and evidence limits. Include omissions, ambiguity, adversarial text, and generation failures.
- [ ] Obtain actual human review/labels; agent-generated labels remain provisional. Do not claim calibration without human-labelled evidence.
- [ ] Add an explicitly invoked live evaluation runner and report with model/runtime/prompt/settings/hardware, dataset size, measured latency, repeated-run consistency, failures, and limitations.
- [ ] If an optional LLM judge is added, compare it with human labels and report false passes/disagreements separately from generation defects. It must never gate approval.
- [ ] Keep ordinary tests independent of model downloads/network access. Record unmet evaluation prerequisites honestly and refresh Phase 08 setup/demo guidance after integration.

## Decision record and handover

Explain model selection based on observed task evidence, resource trade-offs, prompt/schema design, stale-result handling, timeout/retry limits, readiness, and cache strategy. Update this guide, architecture, the ADR index, [build log](../build-log.md), [AI usage](../ai-usage.md), and [project status](../project-status.md); write the handoff.

Stop after Phase 09. If hardware/download access prevents live verification, record the implemented subset and unmet criteria rather than claiming a complete live integration.
