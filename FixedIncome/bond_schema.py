from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict

from FixedIncome.BondTypeEnum import BondTypeEnum
from FixedIncome.DayCountConventionEnum import DayCountConventionEnum


class BondBase(BaseModel):
    symbol: str
    face_value: float
    coupon_rate: float
    maturity_date: date
    issue_date: date
    market_price: float
    bond_type: BondTypeEnum
    frequency: float
    credit_rating: Optional[str]
    day_count_convention: DayCountConventionEnum
    settlement_date: Optional[date]


class BondCreate(BondBase):
    pass


class BondResponse(BondBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
