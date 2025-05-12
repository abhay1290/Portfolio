from typing import List, Optional

from pydantic import Field, model_validator

from FixedIncome.api.bond_schema.BondBaseSchema import BondBaseRequest, BondBaseResponse
from FixedIncome.api.schedule_schema.CallScheduleSchema import CallScheduleEntry
from FixedIncome.api.schedule_schema.CouponScheduleSchema import CouponScheduleEntry
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.CouponFrequencyEnum import CouponFrequencyEnum


# Callable Bond
class CallableBondRequest(BondBaseRequest):
    coupon_rate: Optional[float] = Field(None, ge=0)
    coupon_frequency: Optional[CouponFrequencyEnum]
    coupon_schedule: Optional[List[CouponScheduleEntry]]

    call_schedule: Optional[List[CallScheduleEntry]]

    @model_validator(mode='after')
    def validate_callable_bond(self):
        if self.bond_type != BondTypeEnum.CALLABLE:
            raise ValueError("bond_type must be CALLABLE for this request")
        return self


class CallableBondResponse(BondBaseResponse):
    coupon_rate: float
    coupon_frequency: CouponFrequencyEnum
    coupon_schedule: List[CouponScheduleEntry]

    call_schedule: List[CallScheduleEntry]
