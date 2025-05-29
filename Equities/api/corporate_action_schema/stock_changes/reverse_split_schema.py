# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class ReverseSplitRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.REVERSE_SPLIT)

    # Reverse Split Ratio Information
    reverse_ratio_from: int = Field(..., gt=0, description="Old shares (higher number)")
    reverse_ratio_to: int = Field(..., gt=0, description="New shares (lower number)")
    reverse_multiplier: condecimal(max_digits=10, decimal_places=6) = Field(..., gt=0, lt=1)

    # Key Dates
    announcement_date: Optional[date] = Field(None)
    ex_split_date: date = Field(..., description="Ex-split date")
    effective_date: date = Field(..., description="Effective date")

    # Price and Fractional Information
    price_adjustment_factor: Optional[condecimal(max_digits=10, decimal_places=6)] = Field(None, gt=1)
    cash_in_lieu_rate: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)

    # Additional Information
    reverse_split_reason: Optional[constr(max_length=1000)] = Field(None)
    reverse_split_notes: Optional[constr(max_length=2000)] = Field(None)

    @classmethod
    @field_validator('reverse_ratio_from')
    def validate_reverse_ratio(cls, v, info):
        reverse_to = info.data.get('reverse_ratio_to')
        if reverse_to and v <= reverse_to:
            raise ValueError("reverse_ratio_from must be greater than reverse_ratio_to")
        return v

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
