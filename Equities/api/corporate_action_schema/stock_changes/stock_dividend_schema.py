# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class StockDividendRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.STOCK_DIVIDEND, frozen=True,
                                                 description="Type of corporate action")

    # Stock Dividend Information
    dividend_shares_per_held: condecimal(max_digits=10, decimal_places=6) = Field(..., gt=0,
                                                                                  description="Number of new shares received per share held (must be positive)")
    dividend_percentage: Optional[float] = Field(None, ge=0.0, le=100.0,
                                                 description="Percentage of shares received as dividend (0-100, optional)")

    # Key Dates
    declaration_date: date = Field(..., description="Date when the stock dividend was declared by the company")
    ex_dividend_date: Optional[date] = Field(None,
                                             description="First date when shares trade without the dividend right (optional)")
    distribution_date: date = Field(..., description="Date when the dividend shares are distributed to shareholders")

    # Valuation Information
    fair_market_value: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0,
                                                                                     description="Fair market value per dividend share (optional, must be non-negative)")
    cash_in_lieu_rate: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0,
                                                                                     description="Cash payment rate for fractional shares (optional, must be non-negative)")
    taxable_value: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0,
                                                                                 description="Taxable value per dividend share (optional, must be non-negative)")

    # Additional Information
    stock_dividend_notes: Optional[constr(max_length=2000)] = Field(None,
                                                                    description="Additional notes or details about the stock dividend (optional, max 2000 chars)")

    @classmethod
    @field_validator('dividend_percentage')
    def validate_percentage(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Dividend percentage must be between 0 and 100")
        return v

    model_config = ConfigDict(extra="forbid")


class StockDividendResponse(CorporateActionResponse):
    dividend_shares_per_held: float
    dividend_percentage: Optional[float] = None
    declaration_date: date
    ex_dividend_date: Optional[date] = None
    distribution_date: date
    fair_market_value: Optional[float] = None
    cash_in_lieu_rate: Optional[float] = None
    taxable_value: Optional[float] = None
    stock_dividend_notes: Optional[str] = None
