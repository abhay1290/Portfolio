from typing import List, Optional

from pydantic import Field, model_validator

from FixedIncome.api.bond_schema.BondBaseSchema import BondBaseRequest, BondBaseResponse
from FixedIncome.api.schedule_schema.CouponScheduleSchema import CouponScheduleEntry
from FixedIncome.api.schedule_schema.NotionalScheduleSchema import NotionalScheduleEntry
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.CouponFrequencyEnum import CouponFrequencyEnum


# Sinking Fund Bond
class SinkingFundBondRequest(BondBaseRequest):
    coupon_rate: Optional[float] = Field(None, ge=0)
    coupon_frequency: Optional[CouponFrequencyEnum]
    coupon_schedule: Optional[List[CouponScheduleEntry]]

    notionals_schedule: Optional[List[NotionalScheduleEntry]]

    @model_validator(mode='after')
    def validate_sinking_bond(self):
        if self.bond_type != BondTypeEnum.SINKING_FUND:
            raise ValueError("bond_type must be SINKING_FUND for this request")
        return self


class SinkingFundBondResponse(BondBaseResponse):
    coupon_rate: float
    coupon_frequency: CouponFrequencyEnum
    coupon_schedule: List[CouponScheduleEntry]

    notionals_schedule: List[NotionalScheduleEntry]
