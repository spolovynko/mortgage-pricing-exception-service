"""Provisional golden-candidate labels for the deterministic checklist contract."""

import json
from pathlib import Path

from mortgage_pricing.ai.assessment_contract import available_source_paths
from mortgage_pricing.ai.rubric import evaluate_checklist

DATASET = Path(__file__).parents[1] / "evals" / "phase09" / "golden-candidate-v1.json"


def _merge(base: dict, update: dict) -> dict:
    merged = base.copy()
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def test_provisional_golden_cases_match_rubric_v2_and_have_human_review_pending():
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    assert dataset["status"] == "provisional_assistant_generated_pending_human_review"
    assert dataset["rubric_version"] == "pricing-exception-review-v2"
    assert dataset["repeatability_protocol"]["same_case_repetitions"] == 3
    assert len({case["case_id"] for case in dataset["cases"]}) == len(dataset["cases"])

    for case in dataset["cases"]:
        snapshot = _merge(dataset["default_snapshot"], case["snapshot_overrides"])
        checklist = evaluate_checklist(snapshot)
        expected = case["expected"]
        assert checklist.suggested_outcome == expected["suggested_outcome"], case["case_id"]
        actual_status = {item.criterion_id: item.status for item in checklist.criteria}
        assert actual_status == expected["criteria"], case["case_id"]
        assert set(case["review_checks"]["must_cover_paths"]) <= available_source_paths(snapshot)
        assert case["human_review"]["status"] == "pending", case["case_id"]
        assert case["human_review"]["reviewer"] is None, case["case_id"]
