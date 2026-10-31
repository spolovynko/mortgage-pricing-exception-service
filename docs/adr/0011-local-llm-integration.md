# ADR 0011: Optional local advisory recommendations

- Date: 2026-10-31. Phase 09 / MVP3.
- Status: Implemented and assistant-verified technical release; human semantic evaluation and phase acceptance remain pending.
- Contributor: Codex, following the user's request for streamed recommendation reasons.
- Related: requirements AI scope, AC-08/09, ADRs 0003 and 0010.

## Context and decision

The earlier implementation presented completeness as a suggested approval and then reduced the model to selecting fields. The user requested an aggregated, readable explanation of whether the specific concession is justified. Complete fields establish neither commercial justification nor pricing-policy compliance.

Use the user's selected local Qwen model through PydanticAI native structured output. Prompt v6/report schema v4 produce an advisory recommendation, concise explanation, next checks, and references. The UI streams draft prose into a styled card, with sources and technical details collapsed. Model prose is escaped; only a validated final report is saved separately from decisions.

The server supplies exact submitted-version data, completeness findings, and Decimal rate arithmetic. Approval is excluded from the generated schema when required fields are missing, or a competing-offer request asks for a deeper concession than the reported offer explains. This is an exercise safeguard for advice, not a bank discount limit. A reviewer can independently decide using the existing workflow.

Check output schema, cited paths, numeric grounding, and selected unsupported pricing assertions. Normalize known field names to reader-facing labels and grouped citations to actual fields/findings. Permit one repair after a rejected draft, then report failure. Keep temperature 0, seed 7, thinking disabled, bounded output, one deadline covering queueing/streaming/repair, and two concurrent slots. Runtime digest discovery has a separate maximum five-second timeout. These controls cannot prove semantic truth or determinism. No probabilities or private chain-of-thought are requested.

## Alternatives and consequences

- Field selection/server-only prose was traceable but did not meet the requested advisory experience.
- Unrestricted generated prose produced invented pricing limits in live development checks. Structured output plus validation reduces this risk but does not eliminate semantic errors.
- Actual decision automation and invented pricing/creditworthiness rules remain outside scope. Reviewer decisions are explicit and version-checked.

Prompt/schema/settings changes invalidate the content cache; matching configured inputs replay the same saved assessment. Model tags may change, so the server resolves the installed weights digest before cache lookup and includes it in the key. Saved history remains viewable without a running model. Existing reports and decisions are retained.

## Evidence and remaining work

Contract, citation/numeric checks, bounded repair, versioned persistence, and safe rendering are covered by `tests/test_assessment_contract.py`, `tests/test_ollama_adapter.py`, `tests/test_assessment_stream.py`, and `tests/ui/workspace.test.cjs`. Live outputs are collected by the [explicit evaluator](../../scripts/run_phase09_golden_eval.py) against [candidate v2](../../evals/phase09/golden-candidate-v2.json); local generated reports are gitignored.

Technical acceptance checks, the Docker-only installation path, explicit demo seeding/identity opt-in, safe logs, and release documentation are verified in the [build entry](../build-log.md#2026-10-31---phase-09-local-ai-and-release-polish) and [handoff](../handoffs/phase-09.md). Actual human labels and semantic explanation review remain pending. Earlier v1 field-selection scores do not establish advisory accuracy. Production use requires real pricing policy, verified evidence, organizational authentication, appropriate privacy/retention controls, and accountable human review.
