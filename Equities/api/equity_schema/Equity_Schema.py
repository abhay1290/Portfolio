from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, confloat, conint, constr

from Currency.CurrencyEnum import CurrencyEnum


class EquityBase(BaseModel):
    symbol: constr(min_length=1, max_length=50)
    currency: CurrencyEnum = Field(default=CurrencyEnum.USD)

    market_price: Optional[confloat(ge=0)] = Field(None, description="Latest market price of the equity")
    shares_outstanding: Optional[conint(ge=0)] = Field(None, description="Total number of outstanding shares")
    float_shares: Optional[conint(ge=0)] = Field(None, description="Number of shares available to the public")
    market_cap: Optional[confloat(ge=0)] = Field(None, description="Total market capitalization")

    corporate_action_ids: Optional[List[conint(ge=1)]] = Field(default_factory=list,
                                                               description="List of associated corporate action IDs")

    model_config = ConfigDict(extra="forbid")


class EquityRequest(EquityBase):
    pass


class EquityResponse(EquityBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
