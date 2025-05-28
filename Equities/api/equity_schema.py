from typing import Optional

from pydantic import BaseModel, ConfigDict

from Currency.CurrencyEnum import CurrencyEnum


class EquityBase(BaseModel):
    symbol: str
    company_name: str
    sector: Optional[str]
    industry: Optional[str]
    price: float
    currency: CurrencyEnum
    volume: int


class EquityCreate(EquityBase):
    pass


class EquityResponse(EquityBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
