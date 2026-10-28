# Phase 06 - Optional local LLM integration

- Status: Not started.
- Milestone: MVP3.
- Prerequisite: Phase 05 core container workflow verified.
- Primary ADR to create: `docs/adr/0006-local-llm-integration.md`.
- Handoff to create: `docs/handoffs/phase-06.md`.

## Objective

Add a narrowly defined, real local AI assistant and automatic model setup. Preserve complete human review when assistance is off, downloading, unavailable, or failing.

## Read first

[AGENTS.md](../../AGENTS.md), [requirements](../requirements.md), [architecture](../architecture.md), [engineering guidelines](../python-engineering-guidelines.md), [AI usage](../ai-usage.md), current status, the Phase 05 handoff, and version/container ADRs.

## AI task and boundaries

The live assistant summarises the exact submitted version and flags information missing under a written exercise checklist. It distinguishes reported claims from verified facts. It does not grant a discount, change a status, invent lending policy, or verify outside evidence.

An LLM judge that grades summaries is a separate evaluation component developed/calibrated in Phase 07. Do not conflate that score with approval authority.

## Implementation tasks

- [ ] Define the checklist, structured assessment schema, prompt version, and bounded input/output. Use fields for source references and limitations where useful; exclude approval-writing outputs.
- [ ] Implement a small Ollama adapter with explicit timeout, limited retries, bounded concurrency, and schema/error handling.
- [ ] Add assessment creation/status endpoints and enforce identity/version requirements on the server.
- [ ] Capture version input before inference, avoid holding a database write transaction during inference, and handle a revision/decision occurring while generation is running.
- [ ] Store assessment separately from decisions, with exact request version, model identity/digest, prompt/checklist version, timing, and result state. Old results cannot be presented as current advice.
- [ ] Connect the session toggle and Generate button. Off prevents new calls; existing records remain. Changing the toggle does not control Docker or automatically trigger a call.
- [ ] Implement truthful AI availability states and useful errors. Keep the human workflow and core readiness independent.
- [ ] Add Ollama and model-init services under the ai Compose profile, reusing the existing application Dockerfile/image for the Python setup job.
- [ ] Use a pinned tested Ollama image and a persistent model volume. Starting candidate: `qwen3:4b-instruct-2507-q4_K_M`; verify its current artefact, licence, resource footprint, and actual task performance.
- [ ] In model-init, wait for runtime readiness, inspect the local cache, download only when missing with visible progress, verify the selected model, and perform a small inference readiness check.
- [ ] Use bounded retries with a clear failure result. No permanent startup loop or false ready state.
- [ ] Disable Ollama cloud features for the local-only mode. Publish no unnecessary model port. Never commit weights or bake them into the application image.

## Verification

First run ordinary adapter/API/UI tests with explicit fakes: disabled AI makes no call; timeout, malformed/truncated response, unavailable runtime, stale assessment, and misleading instructions in input are handled safely. Confirm the model cannot alter an approval record.

Then exercise the actual selected model on the actual tested hardware. Record model digest/quantisation, runtime image, settings, context/output limits, hardware, latency, and memory observations. A 16 GB host is a planning recommendation, not a tested minimum or performance promise.

Verify first-run download and cache reuse using isolated test volumes:

```bash
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

## Decision record and handover

Explain model selection based on observed task evidence, resource trade-offs, prompt/schema design, stale-result handling, timeout/retry limits, readiness, and cache strategy. Update this guide, architecture, the ADR index, [build log](../build-log.md), [AI usage](../ai-usage.md), and [project status](../project-status.md); write the handoff.

Stop after Phase 06. If hardware/download access prevents live verification, record the implemented subset and unmet criteria rather than claiming a complete live integration.
