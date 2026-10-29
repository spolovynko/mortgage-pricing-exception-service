"""Validated, non-PII context attached to an exact pricing-request version."""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_serializer


class MortgagePurpose(StrEnum):
    PURCHASE = "purchase"
    REMORTGAGE = "remortgage"
    PRODUCT_TRANSFER = "product_transfer"


class RateType(StrEnum):
    FIXED = "fixed"
    VARIABLE = "variable"
    TRACKER = "tracker"


class ReasonCategory(StrEnum):
    COMPETITIVE_OFFER = "competitive_offer"
    RETENTION = "retention"
    RELATIONSHIP = "relationship"
    OTHER = "other"


CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


class ApplicationDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purpose: MortgagePurpose
    rate_type: RateType
    loan_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    property_value: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency_code: CurrencyCode
    term_months: int = Field(strict=True, gt=0)
    standard_rate_bps: int = Field(strict=True, ge=0)

    @field_serializer("loan_amount", "property_value")
    def serialize_amount(self, amount: Decimal) -> str:
        return format(amount.quantize(Decimal("0.01")), "f")


class CompetitorOffer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rate_bps: int = Field(strict=True, ge=0)
    expires_on: date | None = None


class RequestContext(BaseModel):
    """Optional structured snapshot; all money is in ``currency_code``."""

    model_config = ConfigDict(extra="forbid")

    application: ApplicationDetails
    reason_category: ReasonCategory
    competitor_offer: CompetitorOffer | None = None
