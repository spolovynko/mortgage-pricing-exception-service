# Phase 09 synthetic evaluation set

`golden-candidate-v1.json` is a versioned, synthetic **candidate** set. Its deterministic checklist labels are derived from `pricing-exception-review-v2` and checked offline by `tests/test_phase09_golden_candidate.py`. The source-selection review prompts cover required-field omissions, competitor offers, unverified manager assertions, adversarial instruction text, and limits on conclusions.

The labels are assistant-generated and have not been reviewed by a human. Keep the status as `provisional_assistant_generated_pending_human_review` until an authorized human reviewer checks every case and records reviewer/date/notes in each `human_review` field. Do not cite candidate-set performance as model accuracy or acceptance evidence.

## What this can measure

- **Checklist correctness:** exact comparison of deterministic criterion statuses and suggestion against the candidate labels.
- **Sampled generation repeatability:** exact comparison of the complete model narrative across repeated runs with the same configured model, prompt, rubric, schema, and settings.
- **Evidence selection:** exact comparison of the model-selected field paths against each case's `must_cover_paths`. Schema validation also rejects paths to absent/blank fields. Human review should still judge whether selections are relevant and useful.
- **Report accuracy:** all prose and values are now assembled by the server from the source snapshot and deterministic checklist; the model can only select source paths. Review that displayed values match their cited fields and that no missing field is presented as supplied.
- **Persistence idempotency:** covered separately by the assessment API/persistence test, which repeats an identical assessment request and verifies one model call and the same saved assessment ID.

The model is deliberately not asked to predict approval or produce a probability. The checklist suggestion is an exercise completeness signal, not a credit decision. Source-path validation proves a selected path exists in the submitted version; relevance still needs evaluation.

## Run

Offline contract check:

```powershell
uv run pytest tests/test_phase09_golden_candidate.py -q
```

Live model evaluation (Ollama must already be running with the configured model; it does not download a model):

```powershell
uv run python scripts/run_phase09_golden_eval.py
```

The live runner evaluates every case three times by default and writes a local report under `artifacts/ai-evaluation/`, which is gitignored. Use `--case-id complete_retention --repeats 1` for a small smoke run. Set `--base-url`, `--model`, `--timeout`, or `--output` to override defaults. It requires the model to already be installed in local Ollama and records the Ollama version and selected model digest. The report contains selected paths, assembled reports, host metadata, per-run TTFT/latency/token counts, checklist label matches, evidence-path coverage, exact selection repeatability, and explicit limits. Review selection relevance manually before drawing conclusions.

When human labels change, create a new dataset version, record reviewer and date, preserve the prior file, and rerun both the offline checklist check and explicitly invoked live evaluation. Do not change a label just to make the model pass.
