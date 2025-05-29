# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class StockDividendRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.STOCK_DIVIDEND)

    # Stock Dividend Information
    dividend_shares_per_held: condecimal(max_digits=10, decimal_places=6) = Field(..., gt=0)
    dividend_percentage: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Key Dates
    declaration_date: date = Field(..., description="Declaration date")
    ex_dividend_date: Optional[date] = Field(None, description="Ex-dividend date")
    distribution_date: date = Field(..., description="Distribution date")

    # Valuation Information
    fair_market_value: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)
    cash_in_lieu_rate: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)
    taxable_value: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)

    # Additional Information
    stock_dividend_notes: Optional[constr(max_length=2000)] = Field(None)

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
