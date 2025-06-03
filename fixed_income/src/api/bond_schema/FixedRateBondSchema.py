from datetime import date
from typing import Optional

from pydantic import Field, model_validator

from fixed_income.src.api.bond_schema.BondBaseSchema import BondBaseRequest, BondBaseResponse
from fixed_income.src.model.enums import BondTypeEnum, CalendarEnum, FrequencyEnum


class FixedRateBondRequest(BondBaseRequest):
    coupon_rate: Optional[float] = Field(None, ge=0, description="Annual coupon rate")
    coupon_frequency: Optional[FrequencyEnum] = Field(None, description="Frequency of coupon payments")

    redemption_value: Optional[float] = Field(100.0, ge=0, description="Redemption value as % of face value")
    redemption_date: Optional[date] = Field(None, description="Redemption date if different from maturity")

    ex_coupon_days: Optional[int] = Field(None, ge=0, description="Number of ex-coupon days before coupon date")
    ex_coupon_calendar: Optional[CalendarEnum] = Field(None, description="Calendar for ex-coupon days")

    @model_validator(mode='after')
    def validate_fixed_rate_bond(self):
        # Enforce bond_type
        if self.bond_type != BondTypeEnum.FIXED_COUPON:
            raise ValueError("bond_type must be FIXED_COUPON for this request")

        # coupon_rate and coupon_frequency are required for fixed-rate bonds
        if self.coupon_rate is None:
            raise ValueError("coupon_rate is required for fixed-rate bonds")
        if self.coupon_frequency is None:
            raise ValueError("coupon_frequency is required for fixed-rate bonds")

        # ex_coupon_days and ex_coupon_calendar must be both set or both None
        if (self.ex_coupon_days is None) != (self.ex_coupon_calendar is None):
            raise ValueError("ex_coupon_days and ex_coupon_calendar must be both set or both None")

        return self


class FixedRateBondResponse(BondBaseResponse):
    coupon_rate: float
    coupon_frequency: FrequencyEnum

    redemption_value: float
    redemption_date: Optional[date]

    ex_coupon_days: Optional[int]
    ex_coupon_calendar: Optional[CalendarEnum]
