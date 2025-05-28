from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from Currency.CurrencyEnum import CurrencyEnum
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.BusinessDayConventionEnum import BusinessDayConventionEnum
from FixedIncome.enums.CalenderEnum import CalendarEnum
from FixedIncome.enums.CompoundingEnum import CompoundingEnum
from FixedIncome.enums.DayCountConventionEnum import DayCountConventionEnum
from FixedIncome.enums.FrequencyEnum import FrequencyEnum


class BondBaseRequest(BaseModel):
    # Identifiers
    symbol: Optional[str] = Field(None, max_length=50)
    bond_type: BondTypeEnum = Field(..., description="Required bond type")
    currency: CurrencyEnum = Field(default=CurrencyEnum.USD)

    # Dates
    issue_date: date = Field(..., description="Date bond was issued")
    maturity_date: date = Field(..., description="Bond maturity date")
    evaluation_date: date = Field(..., description="Valuation date/as-of date")
    settlement_days: int = Field(default=2, ge=0, description="Days after eval date for settlement")
    calendar: CalendarEnum = Field(default=CalendarEnum.TARGET, description="Calender followed to find business days")
    business_day_convention: BusinessDayConventionEnum = Field(default=BusinessDayConventionEnum.FOLLOWING,
                                                               description="Business day adjustment convention")

    # Pricing
    face_value: float = Field(default=100.00, gt=0, description="Par value of bond")
    market_price: Optional[float] = Field(default=0.00, gt=0, description="Market price (optional for pricing logic)")

    # Conventions
    day_count_convention: DayCountConventionEnum = Field(default=DayCountConventionEnum.ACTUAL_365_FIXED)
    compounding: CompoundingEnum = Field(default=CompoundingEnum.COMPOUNDED)
    frequency: FrequencyEnum = Field(default=FrequencyEnum.ANNUAL)

    model_config = ConfigDict(extra="forbid")

    @classmethod
    @field_validator("maturity_date")
    def maturity_after_issue(cls, v, info):
        if v <= info.data["issue_date"]:
            raise ValueError("Maturity date must be after issue date")
        return v

    @classmethod
    @field_validator("evaluation_date")
    def eval_before_maturity(cls, v, info):
        if v > info.data["maturity_date"]:
            raise ValueError("Evaluation date must be on or before maturity date")
        return v


class BondBaseResponse(BondBaseRequest):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True)
