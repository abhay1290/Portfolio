# Corporate Action Pydantic Request/Response Models
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class StockSplitRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.STOCK_SPLIT)

    # Split Ratio Information
    split_ratio_from: int = Field(..., gt=0, description="Old shares (denominator)")
    split_ratio_to: int = Field(..., gt=0, description="New shares (numerator)")
    split_multiplier: condecimal(max_digits=10, decimal_places=6) = Field(..., gt=0)

    # Key Dates
    announcement_date: Optional[date] = Field(None, description="Announcement date")
    ex_split_date: date = Field(..., description="Ex-split date")
    effective_date: date = Field(..., description="Effective date")

    # Price and Fractional Share Information
    price_adjustment_factor: Optional[condecimal(max_digits=10, decimal_places=6)] = Field(None, gt=0)
    cash_in_lieu_rate: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)
    fractional_share_treatment: Optional[constr(max_length=100)] = Field(None)

    # Additional Information
    split_notes: Optional[constr(max_length=2000)] = Field(None)

    @classmethod
    @field_validator('split_multiplier')
    def validate_split_multiplier(cls, v, info):
        split_from = info.data.get('split_ratio_from')
        split_to = info.data.get('split_ratio_to')
        if split_from and split_to:
            expected_multiplier = Decimal(str(split_to)) / Decimal(str(split_from))
            if abs(v - expected_multiplier) > Decimal('0.000001'):
                raise ValueError("split_multiplier must equal split_ratio_to / split_ratio_from")
        return v

    model_config = ConfigDict(extra="forbid")


class StockSplitResponse(CorporateActionResponse):
    split_ratio_from: int
    split_ratio_to: int
    split_multiplier: float
    announcement_date: Optional[date] = None
    ex_split_date: date
    effective_date: date
    price_adjustment_factor: Optional[float] = None
    cash_in_lieu_rate: Optional[float] = None
    fractional_share_treatment: Optional[str] = None
    split_notes: Optional[str] = None
