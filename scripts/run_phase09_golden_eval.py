"""Run the explicitly invoked live Phase 09 assessment evaluation on synthetic cases."""

import argparse
import asyncio
import json
import os
import platform
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from mortgage_pricing.ai.assessment_contract import assemble_report
from mortgage_pricing.ai.ollama import AssessmentFailure, stream_assessment
from mortgage_pricing.ai.rubric import evaluate_checklist

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "evals" / "phase09" / "golden-candidate-v1.json"
DEFAULT_OUTPUT = ROOT / "artifacts" / "ai-evaluation" / "phase09-golden-candidate-v1-results.json"


def _merge(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = base.copy()
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _get_ollama_json(base_url: str, endpoint: str) -> dict[str, Any]:
    with urlopen(base_url.rstrip("/") + endpoint, timeout=5) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError(f"Ollama returned invalid metadata from {endpoint}.")
    return payload


async def _run_once(base_url: str, model: str, timeout: float, snapshot, checklist):
    final = None
    metrics = {}
    async for event in stream_assessment(
        base_url=base_url,
        model=model,
        timeout=timeout,
        snapshot=snapshot,
        checklist=checklist.model_dump(mode="json"),
    ):
        if event["type"] == "complete":
            final = event["result"]
            metrics = event.get("metrics", {})
    if final is None:
        raise AssessmentFailure("incomplete_stream")
    return final, metrics


async def run(args: argparse.Namespace) -> dict[str, Any]:
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    runtime = _get_ollama_json(args.base_url, "/api/version")
    inventory = _get_ollama_json(args.base_url, "/api/tags")
    model_record = next(
        (item for item in inventory.get("models", []) if item.get("name") == args.model), None
    )
    if not isinstance(model_record, dict) or not model_record.get("digest"):
        raise ValueError(
            f"Model {args.model!r} is not present in the local Ollama inventory with a digest."
        )
    cases = dataset["cases"]
    if args.case_id:
        cases = [case for case in cases if case["case_id"] in args.case_id]
        found = {case["case_id"] for case in cases}
        missing = sorted(set(args.case_id) - found)
        if missing:
            raise ValueError("Unknown case IDs: " + ", ".join(missing))

    results = []
    for case in cases:
        snapshot = _merge(dataset["default_snapshot"], case["snapshot_overrides"])
        checklist = evaluate_checklist(snapshot)
        expected = case["expected"]
        statuses = {item.criterion_id: item.status for item in checklist.criteria}
        checklist_matches = (
            checklist.suggested_outcome == expected["suggested_outcome"]
            and statuses == expected["criteria"]
        )
        runs = []
        for repetition in range(args.repeats):
            try:
                selection, metrics = await _run_once(
                    args.base_url, args.model, args.timeout, snapshot, checklist
                )
                runs.append(
                    {
                        "repetition": repetition + 1,
                        "selection": selection.model_dump(mode="json"),
                        "report": assemble_report(selection, checklist, snapshot),
                        "metrics": metrics,
                        "error": None,
                    }
                )
            except AssessmentFailure as exc:
                runs.append(
                    {
                        "repetition": repetition + 1,
                        "selection": None,
                        "metrics": {},
                        "error": exc.code,
                    }
                )
        outputs = [run["selection"] for run in runs]
        repeatable = (
            bool(outputs)
            and all(output is not None for output in outputs)
            and all(output == outputs[0] for output in outputs[1:])
        )
        results.append(
            {
                "case_id": case["case_id"],
                "purpose": case["purpose"],
                "expected_checklist": expected,
                "actual_checklist": {
                    "suggested_outcome": checklist.suggested_outcome,
                    "criteria": statuses,
                    "matches_candidate_label": checklist_matches,
                },
                "review_checks": case["review_checks"],
                "runs": runs,
                "repeatable_across_requested_runs": repeatable,
                "required_selection_paths_covered": [
                    all(
                        path in (run["selection"] or {}).get("selected_source_refs", [])
                        for path in case["review_checks"]["must_cover_paths"]
                    )
                    for run in runs
                ],
                "human_selection_relevance": "pending human review",
            }
        )

    repeatable_count = sum(case["repeatable_across_requested_runs"] for case in results)
    covered_paths = sum(sum(case["required_selection_paths_covered"]) for case in results)
    required_paths = sum(len(case["required_selection_paths_covered"]) for case in results)
    return {
        "report_version": 1,
        "dataset_id": dataset["dataset_id"],
        "dataset_status": dataset["status"],
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "runtime_url": args.base_url,
        "model_identity": args.model,
        "model_digest": model_record["digest"],
        "ollama_runtime_version": runtime.get("version"),
        "pydantic_ai_version": version("pydantic-ai-slim"),
        "python_version": platform.python_version(),
        "host_platform": platform.platform(),
        "host_machine": platform.machine(),
        "host_processor": platform.processor() or None,
        "repetitions_per_case": args.repeats,
        "case_count": len(results),
        "checklist_candidate_label_matches": sum(
            case["actual_checklist"]["matches_candidate_label"] for case in results
        ),
        "repeatable_cases": repeatable_count,
        "required_selection_paths_covered": covered_paths,
        "required_selection_path_checks": required_paths,
        "limitations": [
            "Expected labels are provisional assistant-generated labels pending human review.",
            "Narrative accuracy is not automatically scored; review source faithfulness, "
            "omissions, "
            "unsupported claims, and limitations manually.",
            "Repeated output equality over a small sample is not a general determinism guarantee.",
            "This evaluation cannot establish lending suitability, model calibration, "
            "or legal compliance.",
        ],
        "cases": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--model", default="qwen3:4b-instruct-2507-q4_K_M")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--case-id", action="append", help="Run selected case(s); repeat to select several."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.repeats < 1 or args.repeats > 10:
        parser.error("--repeats must be between 1 and 10")
    report = asyncio.run(run(args))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote {report['case_count']} cases to {args.output}. "
        f"Checklist labels match: {report['checklist_candidate_label_matches']}; "
        f"repeatable cases: {report['repeatable_cases']}; "
        f"selected-path checks passed: {report['required_selection_paths_covered']}/"
        f"{report['required_selection_path_checks']}. Human report review remains pending."
    )


if __name__ == "__main__":
    main()
