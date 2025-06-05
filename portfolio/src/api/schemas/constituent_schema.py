# Base Models
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field

from portfolio.src.model.enums import CurrencyEnum


class ConstituentBase(BaseModel):
    symbol: Annotated[str, Field(min_length=1, max_length=20, description="Unique ticker symbol for the constituent")]
    weight: Annotated[Decimal, Field(ge=0, le=1, decimal_places=6, description="Current weight in portfolio")]
    target_weight: Annotated[Optional[Decimal], Field(None, ge=0, le=1, decimal_places=6,
                                                      description="Target weight for rebalancing")]
    outstanding_shares: Annotated[Optional[Decimal], Field(None, decimal_places=6,
                                                           description="Number of units held")]
    currency: Annotated[CurrencyEnum, Field(description="Currency denomination for the constituent")]
    is_active: Annotated[bool, Field(default=True, description="Active status flag")]


class PortfolioEquityRequest(ConstituentBase):
    equity_id: int


class PortfolioBondRequest(ConstituentBase):
    bond_id: int


# Response Models
class PortfolioEquityResponse(ConstituentBase):
    equity_id: int
    market_value: Annotated[Optional[Decimal], Field(None, decimal_places=2)]
    added_at: datetime
    last_rebalanced_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PortfolioBondResponse(ConstituentBase):
    bond_id: int
    market_value: Annotated[Optional[Decimal], Field(None, decimal_places=2)]
    added_at: datetime
    last_rebalanced_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
