"""Versioned, evidence-linked advisory opinions, separate from human decisions."""

import re
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from mortgage_pricing.ai.rubric import ChecklistResult

PROMPT_VERSION = "pricing-exception-advisor-v6"
REPORT_SCHEMA_VERSION = "assessment-report-v4"
GENERATION_SETTINGS = {
    "temperature": 0.0,
    "seed": 7,
    "max_tokens": 600,
    "think": False,
    "keep_alive": "30m",
}


class AdvisoryOpinion(BaseModel):
    """A nonbinding recommendation and short explanation for the human reviewer."""

    model_config = ConfigDict(extra="forbid")
    recommendation: Literal["approve", "do_not_approve", "needs_more_information"]
    explanation: str = Field(min_length=1, max_length=1000)
    next_steps: list[Annotated[str, Field(min_length=1, max_length=220)]] = Field(
        min_length=1, max_length=3
    )
    source_refs: list[str] = Field(min_length=1, max_length=24)


class IncompleteOpinion(AdvisoryOpinion):
    """Constrain generation itself when approval lacks required support."""

    recommendation: Literal["do_not_approve", "needs_more_information"]


_NUMBER = re.compile(r"(?<![A-Za-z0-9_])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")


def reader_language(opinion: AdvisoryOpinion) -> AdvisoryOpinion:
    """Render known internal field labels as plain English without changing their meaning."""
    labels = {
        "checklist.application_context": "application details",
        "checklist.reason_category": "reason category",
        "checklist.reason_present": "submission justification",
        "checklist.request_terms": "requested terms",
        "checklist.competitor_offer": "competing offer details",
        "context.application.standard_rate_bps": "standard rate",
        "context.application.loan_amount": "loan amount",
        "context.application.property_value": "property value",
        "context.application.term_months": "loan term",
        "context.reason_category": "reason category",
        "context.competitor_offer.expires_on": "offer expiry",
        "context.competitor_offer.rate_bps": "reported competing rate",
        "context.competitor_offer": "reported competing offer",
        "context.application": "application details",
        "derived.proposed_rate_bps": "proposed rate",
        "derived.standard_rate_bps": "standard rate",
        "derived.reduction_percentage_points": "requested rate reduction",
    }

    def clean(text: str) -> str:
        text = re.sub(r"\bevidence[ ._]key:?\s*", "", text, flags=re.I)
        for key in sorted(labels, key=len, reverse=True):
            text = text.replace(key, labels[key])
        return text

    update = {}
    if hasattr(opinion, "explanation"):
        update["explanation"] = clean(opinion.explanation)
    if hasattr(opinion, "next_steps"):
        update["next_steps"] = [clean(step) for step in opinion.next_steps]
    return opinion.model_copy(update=update)


def _numbers(value: Any) -> set[Decimal]:
    return {Decimal(match.group().replace(",", "")) for match in _NUMBER.finditer(str(value))}


def validate_opinion_text(opinion: AdvisoryOpinion, catalog: dict[str, Any]) -> None:
    """Reject unsupported numbers and technical/policy inventions; semantics still need review."""
    allowed_numbers = set().union(
        *(_numbers(value) for key, value in catalog.items() if key != "request_id")
    )
    texts = [getattr(opinion, "explanation", "")]
    for text in texts + getattr(opinion, "next_steps", []):
        if _numbers(text) - allowed_numbers:
            raise ValueError("Opinion introduces a numeric claim absent from submitted evidence.")
        if re.search(
            r"(?:context\.|checklist\.|evidence\.key|source_refs|prompt.version)", text, re.I
        ):
            raise ValueError("Opinion prose must use plain language, not internal field names.")
        if re.search(r"(?:typical|usually|standard retention).{0,80}(?:discount|bps)", text, re.I):
            raise ValueError("Remove the unsupported pricing-rule assertion.")
        if re.search(r"(?:probability|confidence|chance of approval).{0,50}\d", text, re.I):
            raise ValueError("Uncalibrated approval probabilities are not supported.")


def source_values(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Map scalar, nonblank submitted values to exact evidence paths."""
    values: dict[str, Any] = {}

    def visit(value: Any, prefix: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                visit(child, f"{prefix}.{key}" if prefix else str(key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{prefix}[{index}]")
        elif value is not None and (not isinstance(value, str) or value.strip()):
            values[prefix] = value

    visit(snapshot, "")
    return values


def available_source_paths(snapshot: dict[str, Any]) -> set[str]:
    return set(source_values(snapshot))


def pricing_effect(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Compute displayed rate arithmetic without assuming bank pricing limits."""
    values = source_values(snapshot)
    standard = values.get("context.application.standard_rate_bps")
    discount = values.get("discount_bps")
    if type(standard) is not int or type(discount) is not int:
        return {}
    proposed = standard - discount
    effect = {
        "standard_rate_bps": standard,
        "reduction_bps": discount,
        "proposed_rate_bps": proposed,
        "reduction_percentage_points": str(Decimal(discount) / 100),
        "description": (
            f"The requested {discount}-basis-point reduction would change the displayed rate "
            f"from {Decimal(standard) / 100:.2f}% to {Decimal(proposed) / 100:.2f}%."
        ),
    }
    competitor = values.get("context.competitor_offer.rate_bps")
    if type(competitor) is int:
        effect["reduction_to_match_reported_offer_bps"] = standard - competitor
        effect["extra_reduction_beyond_reported_offer_bps"] = max(0, competitor - proposed)
    return effect


def evidence_catalog(snapshot: dict[str, Any], checklist: ChecklistResult) -> dict[str, Any]:
    """Include submitted values, deterministic arithmetic, and explicit completeness findings."""
    return (
        source_values(snapshot)
        | {f"derived.{key}": value for key, value in pricing_effect(snapshot).items()}
        | {
            f"checklist.{item.criterion_id}": f"{item.status}: {item.explanation}"
            for item in checklist.criteria
        }
    )


def recommendation_allowed(
    recommendation: str, checklist: ChecklistResult, snapshot: dict[str, Any] | None = None
) -> bool:
    """Completeness cannot justify approval; incompleteness blocks an approve suggestion."""
    if recommendation != "approve":
        return True
    if any(item.status not in ("met", "not_applicable") for item in checklist.criteria):
        return False
    if snapshot and source_values(snapshot).get("context.reason_category") == "competitive_offer":
        return pricing_effect(snapshot).get("extra_reduction_beyond_reported_offer_bps", 0) <= 0
    return True


def normalize_opinion(
    opinion: AdvisoryOpinion, snapshot: dict[str, Any], checklist: ChecklistResult
) -> AdvisoryOpinion:
    """Validate citations and completeness gates without treating path existence as truth."""
    available = evidence_catalog(snapshot, checklist)
    missing_refs = {
        field: f"checklist.{criterion.criterion_id}"
        for criterion in checklist.criteria
        for field in criterion.missing_fields
    }
    refs = []
    for ref in opinion.source_refs:
        path = (
            ref.removeprefix("evidence.")
            .removeprefix("submitted_fields.")
            .removeprefix("submitted_snapshot.")
        )
        path = missing_refs.get(path, path)
        if path not in available:
            group = [item for item in available if item.startswith(path + ".")]
            missing_group = [
                target for field, target in missing_refs.items() if field.startswith(path + ".")
            ]
            if group or missing_group:
                refs.extend(group + missing_group)
                continue
            aliases = [item for item in available if item.endswith("." + path)]
            if len(aliases) != 1:
                raise ValueError(f"Unknown evidence key {path!r}; use only supplied evidence keys.")
            path = aliases[0]
        refs.append(path)
    if not recommendation_allowed(opinion.recommendation, checklist, snapshot):
        raise ValueError(
            "Approval needs resolved completeness and support for the requested amount."
        )
    normalized = reader_language(opinion.model_copy(update={"source_refs": sorted(set(refs))}))
    validate_opinion_text(normalized, available)
    return normalized


def assemble_report(
    opinion: AdvisoryOpinion, checklist: ChecklistResult, snapshot: dict[str, Any]
) -> dict[str, object]:
    """Keep the visible opinion compact and retain the evidence/checklist for inspection."""
    return opinion.model_dump(mode="json") | {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "rubric_version": checklist.rubric_version,
        "pricing_effect": pricing_effect(snapshot).get("description"),
        "criteria": [item.model_dump(mode="json") for item in checklist.criteria],
        "notice": "AI advice based on submitted information. A human reviewer makes the decision.",
    }
