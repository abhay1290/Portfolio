# Corporate Action Pydantic Request/Response Models
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic.types import condecimal, constr

from equity.src.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, \
    CorporateActionResponse
from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class StockSplitRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.STOCK_SPLIT, frozen=True,
                                                 description="Type of corporate action")

    # Split Ratio Information
    split_ratio_from: int = Field(..., gt=0, description="Number of shares before the split (must be positive)")
    split_ratio_to: int = Field(..., gt=0, description="Number of shares after the split (must be positive)")
    split_multiplier: condecimal(max_digits=10, decimal_places=6) = Field(..., gt=1,
                                                                          description="Multiplier representing the split ratio (must be greater than 1)")

    # Key Dates
    announcement_date: Optional[date] = Field(None, description="Date when the stock split was announced (optional)")
    ex_split_date: date = Field(..., description="First date when shares trade post-split")
    effective_date: date = Field(..., description="Date when the split becomes effective")

    # Price and Fractional Share Information
    price_adjustment_factor: Optional[condecimal(max_digits=10, decimal_places=6)] = Field(None, gt=0,
                                                                                           description="Factor to adjust historical prices (optional, must be positive)")
    cash_in_lieu_rate: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0,
                                                                                     description="Cash payment rate for fractional shares (optional, must be non-negative)")
    fractional_share_treatment: Optional[constr(max_length=100)] = Field(None,
                                                                         description="Method for handling fractional shares (optional, max 100 chars)")

    # Additional Information
    split_notes: Optional[constr(max_length=2000)] = Field(None,
                                                           description="Additional notes about the stock split (optional, max 2000 chars)")

    @classmethod
    @field_validator('split_multiplier')
    def validate_split_multiplier(cls, v, info):
        split_from = info.data.get('split_ratio_from')
        split_to = info.data.get('split_ratio_to')
        if split_from and split_to:
            expected_multiplier = Decimal(str(split_to)) / Decimal(str(split_from))
            if abs(v - expected_multiplier) > Decimal('0.000001'):
                raise ValueError("split_multiplier must equal split_ratio_to / split_ratio_from")
        if v <= 1:
            raise ValueError("split_multiplier must be greater than 1")
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
