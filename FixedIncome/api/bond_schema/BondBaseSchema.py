from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from Currency.CurrencyEnum import CurrencyEnum
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.DayCountConventionEnum import DayCountConventionEnum


class BondBaseRequest(BaseModel):
    symbol: Optional[str] = Field(None, max_length=50)
    bond_type: BondTypeEnum = Field(..., description="Required discriminator for polymorphic deserialization")

    currency: Optional[CurrencyEnum]

    issue_date: Optional[date]
    maturity_date: Optional[date]
    settlement_date: Optional[date]
    settlement_days: Optional[int] = Field(None, ge=0)

    credit_rating: Optional[str] = Field(None, max_length=10)

    face_value: Optional[float] = Field(None, ge=0)
    market_price: Optional[float] = Field(None, ge=0)

    day_count_convention: Optional[DayCountConventionEnum]

    model_config = ConfigDict(extra="forbid")  # Prevent unexpected fields

    # TODO add validations for api requests
    @field_validator('maturity_date', 'settlement_date', mode='after')
    def validate_dates(cls, v, info):
        if info.field_name == 'settlement_date' and v and 'issue_date' in info.data:
            if v < info.data['issue_date']:
                raise ValueError("Settlement date cannot be before issue date")
        if info.field_name == 'maturity_date' and v and 'issue_date' in info.data:
            if v <= info.data['issue_date']:
                raise ValueError("Maturity date must be after issue date")
        return v


class BondBaseResponse(BondBaseRequest):
    id: int
    # created_at: datetime
    # updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True)
