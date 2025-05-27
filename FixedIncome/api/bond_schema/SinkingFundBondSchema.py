from datetime import date
from typing import List, Optional

from pydantic import Field, model_validator

from FixedIncome.api.bond_schema.BondBaseSchema import BondBaseRequest, BondBaseResponse
from FixedIncome.api.schedule_schema.NotionalScheduleSchema import NotionalScheduleEntry
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.FrequencyEnum import FrequencyEnum
from FixedIncome.enums.SinkingFundTypeEnum import SinkingFundTypeEnum


# Sinking Fund Bond

class SinkingFundBondRequest(BondBaseRequest):
    coupon_rate: Optional[float] = Field(None, ge=0, description="Annual coupon rate (non-negative)")
    coupon_frequency: Optional[FrequencyEnum] = Field(None, description="Coupon payment frequency")

    notionals_schedule: Optional[List[NotionalScheduleEntry]] = Field(None,
                                                                      description="Amortization schedule for sinking fund")

    sinking_fund_type: Optional[SinkingFundTypeEnum] = Field(default=SinkingFundTypeEnum.FIXED_PERCENTAGE,
                                                             description="Type of sinking fund structure")
    sinking_fund_start_date: Optional[date] = Field(None, description="Start date of sinking fund schedule")

    @model_validator(mode='after')
    def validate_sinking_bond(self):
        if self.bond_type != BondTypeEnum.SINKING_FUND:
            raise ValueError("bond_type must be SINKING_FUND for this request")

        if self.coupon_rate is None:
            raise ValueError("coupon_rate is required for sinking fund bonds")

        if self.coupon_frequency is None:
            raise ValueError("coupon_frequency is required for sinking fund bonds")

        return self


class SinkingFundBondResponse(BondBaseResponse):
    coupon_rate: float
    coupon_frequency: FrequencyEnum

    notionals_schedule: List[NotionalScheduleEntry]

    sinking_fund_type: Optional[SinkingFundTypeEnum]
    sinking_fund_start_date: Optional[date]
