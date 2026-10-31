"""Versioned, server-authored report contract with model-selected source fields."""

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mortgage_pricing.ai.rubric import ChecklistResult

PROMPT_VERSION = "pricing-exception-evidence-selector-v5"
REPORT_SCHEMA_VERSION = "assessment-report-v3"
GENERATION_SETTINGS = {
    "temperature": 0.0,
    "seed": 7,
    "max_tokens": 256,
    "think": False,
    "keep_alive": "30m",
}


class EvidenceSelection(BaseModel):
    """Model output is restricted to paths of populated submitted values."""

    model_config = ConfigDict(extra="forbid")

    selected_source_refs: list[str] = Field(min_length=1, max_length=16)

    @field_validator("selected_source_refs")
    @classmethod
    def refs_are_unique(cls, refs: list[str]) -> list[str]:
        if len(refs) != len(set(refs)):
            raise ValueError("Selected source paths must be unique.")
        return refs


def source_values(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Map scalar, nonblank submitted values to exact dotted evidence paths."""
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
    """Return only paths to populated scalar fields, never containers or missing fields."""
    return set(source_values(snapshot))


def validate_selection_sources(selection: EvidenceSelection, snapshot: dict[str, Any]) -> None:
    """Reject paths that do not identify populated values in the submitted version."""
    available = available_source_paths(snapshot)
    invalid = sorted(set(selection.selected_source_refs) - available)
    if invalid:
        raise ValueError(
            "Selection cites fields absent from the submitted version: " + ", ".join(invalid)
        )


def canonical_source_path(path: str, snapshot: dict[str, Any]) -> str | None:
    """Normalize wrapper prefixes and unambiguous field-name aliases to exact paths."""
    normalized = path.removeprefix("submitted_snapshot.")
    available = available_source_paths(snapshot)
    if normalized in available:
        return normalized
    matches = [candidate for candidate in available if candidate.endswith("." + normalized)]
    return matches[0] if len(matches) == 1 else None


def normalize_selection(
    selection: EvidenceSelection, snapshot: dict[str, Any]
) -> EvidenceSelection:
    """Return exact canonical refs, rejecting missing, ambiguous, or duplicate paths."""
    refs = [canonical_source_path(path, snapshot) for path in selection.selected_source_refs]
    if any(path is None for path in refs):
        invalid = [
            original
            for original, path in zip(selection.selected_source_refs, refs, strict=True)
            if path is None
        ]
        raise ValueError(
            "Selection cites fields absent or ambiguous in the submitted version: "
            + ", ".join(invalid)
        )
    return EvidenceSelection.model_validate({"selected_source_refs": sorted(refs)})


def assemble_report(
    selection: EvidenceSelection,
    checklist: ChecklistResult,
    snapshot: dict[str, Any],
) -> dict[str, object]:
    """Build every factual sentence/value from submitted data and deterministic checks."""
    values = source_values(snapshot)
    selected = [
        {"field": path, "value": values[path], "source_ref": path}
        for path in selection.selected_source_refs
        if path in values
    ]
    request_id = snapshot.get("request_id", "unknown")
    version = snapshot.get("version_number", "unknown")
    discount = snapshot.get("discount_bps")
    reason = snapshot.get("reason")
    request_line = f"Request {request_id}, version {version}."
    discount_line = (
        f"Submitted discount: {discount} basis points."
        if discount is not None
        else "No discount value was submitted."
    )
    reason_line = (
        "Manager-stated reason (unverified): " + json.dumps(reason, ensure_ascii=False) + "."
        if isinstance(reason, str) and reason.strip()
        else "No submission reason supplied."
    )
    missing_information = [
        {"item": field, "reason": result.explanation}
        for result in checklist.criteria
        for field in result.missing_fields
    ]
    return {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "rubric_version": checklist.rubric_version,
        "criteria": [item.model_dump(mode="json") for item in checklist.criteria],
        "suggested_outcome": checklist.suggested_outcome,
        "outcome_rationale": checklist.outcome_rationale,
        "summary": " ".join((request_line, discount_line, reason_line)),
        "selected_source_refs": selection.selected_source_refs,
        "selected_evidence": selected,
        "missing_information": missing_information,
        "limitations": [
            "Selected values are copied from the submitted request version and are unverified.",
            "The exercise checklist assesses completeness only; it is not a lending decision.",
        ],
    }
