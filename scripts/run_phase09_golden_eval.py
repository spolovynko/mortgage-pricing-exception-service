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

from mortgage_pricing.ai.assessment_contract import (
    GENERATION_SETTINGS,
    PROMPT_VERSION,
    REPORT_SCHEMA_VERSION,
    assemble_report,
)
from mortgage_pricing.ai.ollama import AssessmentFailure, stream_assessment
from mortgage_pricing.ai.rubric import evaluate_checklist

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "evals" / "phase09" / "golden-candidate-v2.json"
DEFAULT_OUTPUT = ROOT / "artifacts" / "ai-evaluation" / "phase09-advisory-v2-results.json"


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
        runs = []
        for repetition in range(args.repeats):
            try:
                opinion, metrics = await _run_once(
                    args.base_url, args.model, args.timeout, snapshot, checklist
                )
                runs.append(
                    {
                        "repetition": repetition + 1,
                        "opinion": opinion.model_dump(mode="json"),
                        "report": assemble_report(opinion, checklist, snapshot),
                        "metrics": metrics,
                        "matches_candidate_recommendation": opinion.recommendation
                        in case["expected_recommendations"],
                        "error": None,
                    }
                )
            except AssessmentFailure as exc:
                runs.append(
                    {
                        "repetition": repetition + 1,
                        "opinion": None,
                        "metrics": {},
                        "matches_candidate_recommendation": False,
                        "error": exc.code,
                        "validation_detail": exc.detail,
                    }
                )
        outputs = [item["opinion"] for item in runs]
        complete = all(output is not None for output in outputs)
        exact_repeatable = complete and all(output == outputs[0] for output in outputs[1:])
        recommendations = [output["recommendation"] for output in outputs if output is not None]
        results.append(
            {
                "case_id": case["case_id"],
                "expected_recommendations": case["expected_recommendations"],
                "human_review_focus": case["human_review_focus"],
                "runs": runs,
                "exact_output_repeatable": exact_repeatable,
                "recommendation_repeatable": complete and len(set(recommendations)) == 1,
                "human_reasoning_quality": "pending human review",
            }
        )

    all_runs = [item for case in results for item in case["runs"]]
    return {
        "report_version": 2,
        "dataset_id": dataset["dataset_id"],
        "dataset_status": dataset["status"],
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "runtime_url": args.base_url,
        "model_identity": args.model,
        "model_digest": model_record["digest"],
        "ollama_runtime_version": runtime.get("version"),
        "pydantic_ai_version": version("pydantic-ai-slim"),
        "prompt_version": PROMPT_VERSION,
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "generation_settings": GENERATION_SETTINGS,
        "python_version": platform.python_version(),
        "host_platform": platform.platform(),
        "host_machine": platform.machine(),
        "host_processor": platform.processor() or None,
        "repetitions_per_case": args.repeats,
        "case_count": len(results),
        "run_count": len(all_runs),
        "validated_runs": sum(not item["error"] for item in all_runs),
        "recommendation_label_matches": sum(
            item["matches_candidate_recommendation"] for item in all_runs
        ),
        "recommendation_repeatable_cases": sum(
            case["recommendation_repeatable"] for case in results
        ),
        "exact_output_repeatable_cases": sum(case["exact_output_repeatable"] for case in results),
        "limitations": [
            "Advisory labels are provisional assistant proposals pending human review.",
            "Citation existence and numeric checks cannot establish full semantic faithfulness.",
            "Narrative quality and evidence support require human review. "
            "No accuracy or calibration claim is established.",
            "Earlier v1 source-selection and completeness scores do not measure "
            "advisory reasoning quality.",
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
        f"Wrote {report['case_count']} cases / {report['run_count']} runs to {args.output}. "
        f"Validated: {report['validated_runs']}; candidate recommendation matches: "
        f"{report['recommendation_label_matches']}. Human reasoning review remains pending."
    )


if __name__ == "__main__":
    main()
