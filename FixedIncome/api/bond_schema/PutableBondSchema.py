from typing import List, Optional

from pydantic import Field, model_validator

from FixedIncome.api.bond_schema.BondBaseSchema import BondBaseRequest, BondBaseResponse
from FixedIncome.api.schedule_schema.CouponScheduleSchema import CouponScheduleEntry
from FixedIncome.api.schedule_schema.PutScheduleSchema import PutScheduleEntry
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.CouponFrequencyEnum import CouponFrequencyEnum


# Putable Bond
class PutableBondRequest(BondBaseRequest):
    coupon_rate: Optional[float] = Field(None, ge=0)
    coupon_frequency: Optional[CouponFrequencyEnum]
    coupon_schedule: Optional[List[CouponScheduleEntry]]

    put_schedule: Optional[List[PutScheduleEntry]]

    @model_validator(mode='after')
    def validate_putable_bond(self):
        if self.bond_type != BondTypeEnum.PUTABLE:
            raise ValueError("bond_type must be PUTABLE for this request")
        return self


class PutableBondResponse(BondBaseResponse):
    coupon_rate: float
    coupon_frequency: CouponFrequencyEnum
    coupon_schedule: List[CouponScheduleEntry]

    put_schedule: List[PutScheduleEntry]
