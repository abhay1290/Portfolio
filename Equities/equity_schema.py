from typing import Optional

from pydantic import BaseModel

from Currency.CurrencyEnum import CurrencyEnum
from Identifier.AssetClassEnum import AssetClassEnum

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

    model_config = {
        "from_attributes": True  # Enable attribute mapping for ORM
    }

    @classmethod
    def from_orm(cls, obj):
        return cls.model_validate(obj)
