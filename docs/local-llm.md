# Optional local LLM

## Docker setup and use

The reviewer only needs Docker and a browser. From the repository root:

```powershell
$env:LLM_MODE = 'auto'
docker compose --profile ai up --build --detach
docker compose --profile ai logs --follow model-init
```

Compose pulls the official pinned `ollama/ollama:0.40.13` image and runs a bounded setup job using the same application image. The selected `qwen3:4b-instruct-2507-q4_K_M` model is downloaded only if absent. Setup prints download progress, verifies the local inventory, and performs a small inference check. Wait for the ready message. Failure does not block the core application; inspect setup logs and continue manual review if needed.

Weights persist in `model-cache`; requests and decisions use a different `application-data` volume. The app uses the private Docker address `http://ollama:11434`. Ollama is not published to the host. Cloud features are disabled for this profile. The model is optional, several GB in size, and never baked into the app image. CPU-only cold starts and response times depend on hardware; the configured container generation deadline is 120 seconds by default. A synthetic CPU-only Docker check on the recorded host took about 14 seconds; see [measured evidence](build-log.md#2026-10-31---phase-09-local-ai-and-release-polish), not a performance guarantee.

In the app, select Reviewer, open a pending request, turn AI on for the session, and click **Get AI recommendation**. The report streams a clearly marked draft, then displays the validated recommendation, concise explanation, and checks before deciding. Sources, model identity, and timing are in optional details. Only the human Approve/Decline buttons record a decision.

To disable new AI requests:

```powershell
$env:LLM_MODE = 'off'
docker compose up --detach app
docker compose --profile ai stop model-init ollama
```

This preserves saved assessments and cached weights. The UI session toggle also prevents new calls but does not control Docker services.

## What is sent and how advice is constrained

The server authorizes the reviewer and captures the exact submitted version. The payload contains request/version identity, requested discount and manager reason, populated structured loan/offer fields, deterministic completeness findings, and exact displayed-rate arithmetic. Previous decisions, unrelated applications, and external customer information are not added. Free text remains untrusted, manager-reported data; do not enter real personal information in the demo.

PydanticAI uses Ollama's local OpenAI-compatible API with native structured output. The prompt requests a nonbinding recommendation (`approve`, `do_not_approve`, or `needs_more_information`), a short explanation, next checks, and source references. Complete fields alone do not justify a discount. Generic retention wording should lead to a request for justification.

The server excludes approval from the generation schema when required evidence is missing or a reported competing rate does not explain the full requested reduction. This is an exercise advisory safeguard, not a bank pricing rule. It validates source references and numeric grounding, rejects selected unsupported policy statements, normalizes known technical labels for display, and allows at most one repair of invalid output. Final reports are saved separately from human decisions; in-flight revisions/decisions can make a result stale. A draft is not a saved result.

Temperature is 0, seed 7, thinking disabled, output capped at 600 tokens, and concurrency bounded to two generations. The whole generation, including queueing and repair, has one configured deadline. These settings do not guarantee identical fresh generations or eliminate semantic errors. No approval probability or private chain-of-thought is requested. No real bank policy or claim verification is provided.

## Cache, audit, and evaluation

Before inference the server resolves the installed model digest. The idempotency key covers the exact snapshot, model name/digest, runtime endpoint, prompt, rubric, schema, and generation settings. Identical configured inputs reuse the saved assessment; changed weights or contracts create a new key. Viewing saved history does not require a live model. A new generation/replay request needs a reachable runtime to resolve its digest.

Saved reports retain model/digest, contract versions, timing/count metrics, references, and recommendation state. Operational JSON logs record safe IDs, outcomes, durations, and error codes, without request reasons, prompts, generated prose, or credentials.

Run the explicit synthetic evaluator from a developer environment with a reachable runtime:

```powershell
uv run python scripts/run_phase09_golden_eval.py
```

The active [candidate v2](../evals/phase09/golden-candidate-v2.json) and [protocol](../evals/phase09/README.md) distinguish label agreement, recommendation consistency, exact prose repeatability, and human semantic review. Candidate labels remain provisional. Ordinary tests make no real model calls. Earlier v1 field-selection scores do not establish advisory accuracy; no legal-compliance or calibration claim is made.

## Native Ollama alternative

A local Python developer can install [Ollama](https://docs.ollama.com/quickstart) and pull the same model with its CLI:

```powershell
ollama pull qwen3:4b-instruct-2507-q4_K_M
$env:LLM_MODE = 'auto'
$env:LLM_BASE_URL = 'http://127.0.0.1:11434'
```

Keep the Ollama app/server running, then launch Uvicorn using the installation guide. Native Ollama and a Docker Ollama volume are separate caches. A model installed in one is not automatically present in the other. The Docker-only reviewer path above needs neither this installation nor Python.

## Failures

- `ai_disabled`: enable `LLM_MODE=auto` on the app process and enable the UI session toggle.
- `model_missing`: wait for `model-init`, check its logs, and verify `LLM_MODEL` matches the installed tag.
- `runtime_unavailable`: check `docker compose --profile ai ps` and the internal URL; localhost inside a container is that container.
- `timeout`: cold loads/CPU inference may exceed the deadline; inspect timings and adjust the bounded timeout if the hardware permits. Human review stays available.
- `invalid_assessment_output`: output failed validation after the bounded repair; it is not saved as valid advice. Retry or decide manually from the submitted facts.
- A stale result is hidden; reload the current version and request new advice.
