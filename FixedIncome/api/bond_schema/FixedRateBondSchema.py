from typing import List, Optional

from pydantic import Field, model_validator

from FixedIncome.api.bond_schema.BondBaseSchema import BondBaseRequest, BondBaseResponse
from FixedIncome.api.schedule_schema.CouponScheduleSchema import CouponScheduleEntry
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.CouponFrequencyEnum import CouponFrequencyEnum


class FixedRateBondRequest(BondBaseRequest):
    coupon_rate: Optional[float] = Field(None, ge=0, description="Annual coupon rate")
    coupon_frequency: Optional[CouponFrequencyEnum] = Field(description="Frequency of coupon payments")
    coupon_schedule: Optional[List[CouponScheduleEntry]] = Field(description="Detailed coupon payment schedule")

    @model_validator(mode='after')
    def validate_fixed_rate_bond(self):
        if self.bond_type != BondTypeEnum.FIXED_COUPON:
            raise ValueError("bond_type must be FIXED_COUPON for this request")
        return self


class FixedRateBondResponse(BondBaseResponse):
    coupon_rate: float
    coupon_frequency: CouponFrequencyEnum
    coupon_schedule: List[CouponScheduleEntry]
