# Corporate Action Pydantic Request/Response Models
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import ConfigDict, Field, model_validator
from pydantic.types import constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class ReverseSplitRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.REVERSE_SPLIT, frozen=True,
                                                 description="Type of corporate action")

    # Reverse Split Ratio Information
    reverse_ratio_from: Annotated[int, Field(default=2, gt=0,
                                             description="Number of shares before reverse split (must be greater than reverse_ratio_to)")]
    reverse_ratio_to: Annotated[int, Field(default=1, gt=0,
                                           description="Number of shares after reverse split (must be less than reverse_ratio_from)")]
    reverse_multiplier: Annotated[Decimal, Field(default=0.5, max_digits=10, decimal_places=6, gt=0, lt=1,
                                                 description="Ratio of new shares to old shares (must be between 0 and 1)")]

    # Key Dates
    announcement_date: Optional[date] = Field(None, description="Date when reverse split was announced")
    ex_split_date: Annotated[date, Field(..., description="First trading date where shares trade post-reverse split")]
    effective_date: Annotated[date, Field(..., description="Date when reverse split becomes effective")]

    # Price and Fractional Information
    price_adjustment_factor: Optional[Annotated[Decimal, Field(default=1.5, max_digits=10, decimal_places=6, gt=1,
                                                               description="Factor by which prices should be adjusted (old_price * factor)")]] = None
    cash_in_lieu_rate: Optional[Annotated[Decimal, Field(..., max_digits=20, decimal_places=6, ge=0,
                                                         description="Cash payment for fractional shares")]] = None

    # Additional Information
    reverse_split_reason: Optional[Annotated[
        constr(max_length=1000, strip_whitespace=True), Field(description="Reason for the reverse split")]] = None
    reverse_split_notes: Optional[Annotated[constr(max_length=2000, strip_whitespace=True), Field(
        description="Additional notes about the reverse split")]] = None

    @model_validator(mode='after')
    def validate_ratios(self):
        if self.reverse_ratio_from <= self.reverse_ratio_to:
            raise ValueError("reverse_ratio_from must be greater than reverse_ratio_to")
        if not (0 < self.reverse_multiplier < 1):
            raise ValueError("reverse_multiplier must be between 0 and 1")

    @model_validator(mode='after')
    def validate_dates(self):
        if self.ex_split_date > self.effective_date:
            raise ValueError("ex_split_date must be before effective_date")

    model_config = ConfigDict(extra="forbid")


class ReverseSplitResponse(CorporateActionResponse):
    reverse_ratio_from: int
    reverse_ratio_to: int
    reverse_multiplier: float
    announcement_date: Optional[date] = None
    ex_split_date: date
    effective_date: date
    price_adjustment_factor: Optional[float] = None
    cash_in_lieu_rate: Optional[float] = None
    reverse_split_reason: Optional[str] = None
    reverse_split_notes: Optional[str] = None
