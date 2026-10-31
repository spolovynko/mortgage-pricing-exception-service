"""Deterministic checklist and human-readable report assembly checks."""

from mortgage_pricing.ai.assessment_contract import (
    AdvisoryOpinion,
    assemble_report,
    normalize_opinion,
    pricing_effect,
)
from mortgage_pricing.ai.rubric import RUBRIC_VERSION, evaluate_checklist


def test_complete_exercise_context_suggests_only_checklist_completeness():
    snapshot = {
        "request_id": "synthetic-1",
        "version_number": 1,
        "discount_bps": 25,
        "reason": "Synthetic retention request",
        "context": {
            "reason_category": "retention",
            "application": {
                "purpose": "purchase",
                "rate_type": "fixed",
                "loan_amount": 200000,
                "property_value": 300000,
                "currency_code": "EUR",
                "term_months": 240,
                "standard_rate_bps": 400,
            },
        },
    }
    result = evaluate_checklist(snapshot)
    assert result.rubric_version == RUBRIC_VERSION
    assert result.suggested_outcome == "suggest_approve"
    assert "does not assess pricing suitability" in result.outcome_rationale


def test_missing_context_and_unknown_category_suggest_do_not_approve():
    result = evaluate_checklist({"request_id": "synthetic-2", "reason": "synthetic"})
    assert result.suggested_outcome == "suggest_do_not_approve"
    assert {item.status for item in result.criteria} >= {"missing", "unknown"}
    assert any("context.reason_category" in item.missing_fields for item in result.criteria)


def test_report_keeps_model_explanation_and_human_decision_separate():
    snapshot = {
        "request_id": "synthetic-3",
        "version_number": 2,
        "discount_bps": 25,
        "reason": "Retention",
    }
    opinion = AdvisoryOpinion(
        recommendation="needs_more_information",
        explanation=(
            "The stated retention intention does not explain why this concession is needed."
        ),
        next_steps=["Ask the manager to support the retention rationale."],
        source_refs=["reason", "checklist.application_context"],
    )
    checklist = evaluate_checklist(snapshot)
    report = assemble_report(normalize_opinion(opinion, snapshot, checklist), checklist, snapshot)
    assert report["recommendation"] == "needs_more_information"
    assert report["explanation"] == opinion.explanation
    assert "human reviewer" in report["notice"]
    assert "suggested_outcome" not in report
    assert "selected_evidence" not in report


def test_rate_arithmetic_is_exact_and_does_not_add_policy_thresholds():
    snapshot = {"discount_bps": 25, "context": {"application": {"standard_rate_bps": 415}}}
    effect = pricing_effect(snapshot)
    assert effect["proposed_rate_bps"] == 390
    assert "4.15% to 3.90%" in effect["description"]


def test_competing_offer_alone_does_not_justify_a_deeper_concession():
    import pytest

    snapshot = {
        "request_id": "synthetic-offer",
        "version_number": 1,
        "discount_bps": 25,
        "reason": "Match a reported competing offer.",
        "context": {
            "reason_category": "competitive_offer",
            "application": {
                "purpose": "purchase",
                "rate_type": "fixed",
                "loan_amount": 200000,
                "property_value": 300000,
                "currency_code": "EUR",
                "term_months": 240,
                "standard_rate_bps": 400,
            },
            "competitor_offer": {"rate_bps": 390, "expires_on": "2027-01-31"},
        },
    }
    effect = pricing_effect(snapshot)
    assert effect["reduction_to_match_reported_offer_bps"] == 10
    assert effect["extra_reduction_beyond_reported_offer_bps"] == 15
    opinion = AdvisoryOpinion(
        recommendation="approve",
        explanation="The reported offer supports this concession.",
        next_steps=["Verify the reported offer."],
        source_refs=["context.competitor_offer.rate_bps"],
    )
    with pytest.raises(ValueError, match="support for the requested amount"):
        normalize_opinion(opinion, snapshot, evaluate_checklist(snapshot))
