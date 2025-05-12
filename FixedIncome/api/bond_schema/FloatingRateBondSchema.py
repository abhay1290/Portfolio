from typing import List, Optional

from pydantic import Field, model_validator

from FixedIncome.api.bond_schema.BondBaseSchema import BondBaseRequest, BondBaseResponse
from FixedIncome.api.schedule_schema.CouponScheduleSchema import CouponScheduleEntry
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.CouponFrequencyEnum import CouponFrequencyEnum


# Floating Rate Bond
class FloatingRateBondRequest(BondBaseRequest):
    coupon_rate: Optional[float] = Field(None, ge=0)
    coupon_frequency: Optional[CouponFrequencyEnum]
    coupon_schedule: Optional[List[CouponScheduleEntry]]

    reference_index: Optional[str] = Field(None, max_length=50)

    @model_validator(mode='after')
    def validate_floating_bond(self):
        if self.bond_type != BondTypeEnum.FLOATING:
            raise ValueError("bond_type must be FLOATING for this request")
        return self


class FloatingRateBondResponse(BondBaseResponse):
    coupon_rate: float
    coupon_frequency: CouponFrequencyEnum
    coupon_schedule: List[CouponScheduleEntry]

    reference_index: str
