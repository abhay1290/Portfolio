from typing import Optional

from pydantic import BaseModel

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

    class Config:
        orm_mode = True


class EquityResponse(EquityBase):
    id: int

    class Config:
        orm_mode = True
