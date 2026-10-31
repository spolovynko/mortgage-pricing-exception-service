# Phase 09 advisory evaluation

The active dataset is `golden-candidate-v2.json`, with ten synthetic cases and provisional assistant-generated recommendation labels. It evaluates concise advisory opinions rather than the earlier field-selection task. Human acceptance of labels and semantic review remain pending.

The model returns an advisory recommendation, a short explanation, next steps, and source references. The backend supplies exact rate arithmetic, excludes approval from the generation schema when required information is incomplete or the reported competing rate does not explain the requested reduction, checks citations and numeric claims, and allows one repair of rejected output. Known field labels in prose are rendered in plain English. None of these checks proves complete semantic faithfulness.

Cases cover weak retention justification, incomplete context, a matching reported competitor offer, incomplete offer evidence, adversarial instructions, invalid terms, and a concession exceeding the reported offer. An `approve` label means a conditional advisory view based on submitted evidence; it never records or authorizes a human decision. The deeper-concession rule is an exercise advisory safeguard, not a bank pricing threshold.

Run the explicit live evaluation against an already installed local model:

```powershell
uv run python scripts/run_phase09_golden_eval.py
```

The default is three direct model runs per case. Use `--case-id vague_retention --repeats 1` for a small run. `--base-url`, `--model`, `--timeout`, and `--output` can override the defaults. The local report `artifacts/ai-evaluation/phase09-advisory-v2-results.json` is gitignored. It records model digest, runtime/prompt/schema/settings, per-run output and latency, validation failures, candidate-label agreement, recommendation consistency, and exact text repeatability.

Interpret the metrics carefully:

- Candidate-label agreement is a regression measure against provisional labels, not independently established accuracy.
- Recommendation consistency and exact prose repeatability are different measurements. Identical wording is not required for a faithful explanation.
- API idempotency is tested separately: repeating identical configured assessment inputs returns the same saved assessment without another model call.
- Human review must examine the explanation, evidence support, unverified claims, usefulness of next steps, and absence of invented pricing rules. No approval probabilities or private chain-of-thought are produced.

The v1 dataset remains historical evidence for the prior completeness/field-selection implementation. Its scores do not apply to the new advisory task. Do not change expected labels to hide model failures; preserve versions and record human reviewer/date/notes when labels are actually reviewed.

Observed native and Docker checks, model/runtime/hardware, material failures, and limits are recorded once in the [Phase 09 build entry](../../docs/build-log.md#2026-10-31---phase-09-local-ai-and-release-polish). Technical checks do not promote provisional labels to human-approved gold.
