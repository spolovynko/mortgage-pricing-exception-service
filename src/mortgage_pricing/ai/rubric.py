"""Versioned, deterministic exercise checklist for pricing exception assessments."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RUBRIC_VERSION = "pricing-exception-review-v2"

APPLICATION_FIELDS = (
    "purpose",
    "rate_type",
    "loan_amount",
    "property_value",
    "currency_code",
    "term_months",
    "standard_rate_bps",
)


class CriterionResult(BaseModel):
    """A deterministic checklist result with paths back to the submitted snapshot."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: Literal[
        "request_terms",
        "reason_present",
        "reason_category",
        "application_context",
        "competitor_offer",
    ]
    status: Literal["met", "missing", "unknown", "not_applicable"]
    explanation: str = Field(min_length=1, max_length=500)
    evidence_refs: list[str] = Field(max_length=12)
    missing_fields: list[str] = Field(max_length=12)


class ChecklistResult(BaseModel):
    """Checklist findings and a nonbinding outcome computed without model prose."""

    model_config = ConfigDict(extra="forbid")

    rubric_version: str = RUBRIC_VERSION
    criteria: list[CriterionResult] = Field(min_length=5, max_length=5)
    suggested_outcome: Literal["suggest_approve", "suggest_do_not_approve"]
    outcome_rationale: str = Field(min_length=1, max_length=500)


def evaluate_checklist(snapshot: dict[str, object]) -> ChecklistResult:
    """Evaluate only the agreed exercise completeness checks, never lending suitability."""
    request_id = snapshot.get("request_id")
    version = snapshot.get("version_number")
    discount = snapshot.get("discount_bps")
    missing_terms = [
        field
        for field, value in (
            ("request_id", request_id),
            ("version_number", version),
            ("discount_bps", discount),
        )
        if value in (None, "") or (field == "discount_bps" and value <= 0)
    ]
    results = [
        CriterionResult(
            criterion_id="request_terms",
            status="missing" if missing_terms else "met",
            explanation=(
                "Missing or invalid submitted terms: " + ", ".join(missing_terms) + "."
                if missing_terms
                else "Request identifier, version, and positive discount are recorded."
            ),
            evidence_refs=[
                f
                for f, value in (
                    ("request_id", request_id),
                    ("version_number", version),
                    ("discount_bps", discount),
                )
                if value not in (None, "")
            ],
            missing_fields=missing_terms,
        )
    ]

    reason = snapshot.get("reason")
    results.append(
        CriterionResult(
            criterion_id="reason_present",
            status="met" if isinstance(reason, str) and reason.strip() else "missing",
            explanation=(
                "A submission reason is recorded."
                if isinstance(reason, str) and reason.strip()
                else "A non-empty submission reason is required."
            ),
            evidence_refs=["reason"] if isinstance(reason, str) and reason.strip() else [],
            missing_fields=[] if isinstance(reason, str) and reason.strip() else ["reason"],
        )
    )

    context = snapshot.get("context")
    context = context if isinstance(context, dict) else None
    category = context.get("reason_category") if context else None
    results.append(
        CriterionResult(
            criterion_id="reason_category",
            status="met" if isinstance(category, str) and category else "missing",
            explanation=(
                "A structured request reason category is recorded."
                if isinstance(category, str) and category
                else "A structured request reason category is required."
            ),
            evidence_refs=["context.reason_category"] if category else [],
            missing_fields=[] if category else ["context.reason_category"],
        )
    )

    application = context.get("application") if context else None
    if isinstance(application, dict):
        missing_application = [
            f"context.application.{field}"
            for field in APPLICATION_FIELDS
            if application.get(field) in (None, "")
        ]
        application_refs = [
            f"context.application.{field}"
            for field in APPLICATION_FIELDS
            if application.get(field) not in (None, "")
        ]
    else:
        missing_application = ["context.application"]
        application_refs = []
    results.append(
        CriterionResult(
            criterion_id="application_context",
            status="missing" if missing_application else "met",
            explanation=(
                "Missing required application context: " + ", ".join(missing_application) + "."
                if missing_application
                else "All required exercise application context fields are present."
            ),
            evidence_refs=application_refs,
            missing_fields=missing_application,
        )
    )

    offer = context.get("competitor_offer") if context else None
    if category == "competitive_offer":
        offer = offer if isinstance(offer, dict) else {}
        missing_offer = [
            f"context.competitor_offer.{field}"
            for field in ("rate_bps", "expires_on")
            if offer.get(field) in (None, "")
        ]
        offer_refs = [
            f"context.competitor_offer.{field}"
            for field in ("rate_bps", "expires_on")
            if offer.get(field) not in (None, "")
        ]
        offer_status = "missing" if missing_offer else "met"
        offer_explanation = (
            "A claimed competing offer needs a submitted rate and expiry; missing: "
            + ", ".join(missing_offer)
            + "."
            if missing_offer
            else "The claimed competing offer has a submitted rate and expiry."
        )
    elif category:
        missing_offer = []
        offer_refs = []
        offer_status = "not_applicable"
        offer_explanation = "No competing offer is claimed by the structured reason category."
    else:
        missing_offer = []
        offer_refs = []
        offer_status = "unknown"
        offer_explanation = (
            "Cannot determine whether competitor-offer details are required until the reason "
            "category is supplied."
        )
    results.append(
        CriterionResult(
            criterion_id="competitor_offer",
            status=offer_status,
            explanation=offer_explanation,
            evidence_refs=offer_refs,
            missing_fields=missing_offer,
        )
    )

    incomplete = [result for result in results if result.status in ("missing", "unknown")]
    if incomplete:
        details = "; ".join(f"{result.criterion_id}: {result.explanation}" for result in incomplete)
        return ChecklistResult(
            criteria=results,
            suggested_outcome="suggest_do_not_approve",
            outcome_rationale=(
                "Exercise checklist information is incomplete; obtain or verify the listed items. "
                + details
            )[:500],
        )
    return ChecklistResult(
        criteria=results,
        suggested_outcome="suggest_approve",
        outcome_rationale=(
            "The submitted fields meet this exercise completeness checklist. This does not "
            "assess pricing suitability, verify claims, or replace a human decision."
        ),
    )
