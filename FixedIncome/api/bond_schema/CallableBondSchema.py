from typing import List, Optional

from pydantic import Field, model_validator

from FixedIncome.api.bond_schema.BondBaseSchema import BondBaseRequest, BondBaseResponse
from FixedIncome.api.schedule_schema.CallScheduleSchema import CallScheduleEntry
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.FrequencyEnum import FrequencyEnum


# Callable Bond
class CallableBondRequest(BondBaseRequest):
    coupon_rate: Optional[float] = Field(None, ge=0)
    coupon_frequency: Optional[FrequencyEnum]

    call_schedule: Optional[List[CallScheduleEntry]]

    call_protection_period_days: Optional[int] = Field(None, ge=0)
    call_notice_period_days: Optional[int] = Field(None, ge=0)
    call_premium: Optional[float] = Field(None, ge=0)

    is_american_call: Optional[bool] = False
    is_bermudan_call: Optional[bool] = False

    @model_validator(mode='after')
    def validate_callable_bond(self):
        # bond_type must be CALLABLE
        if self.bond_type != BondTypeEnum.CALLABLE:
            raise ValueError("bond_type must be CALLABLE for this request")

        # coupon_rate is required for callable bonds
        if self.coupon_rate is None:
            raise ValueError("coupon_rate is required for callable bonds")

        # coupon_frequency is required for callable bonds
        if self.coupon_frequency is None:
            raise ValueError("coupon_frequency is required for callable bonds")

        # Validate call_schedule presence if any callability flags are true
        if (self.is_american_call or self.is_bermudan_call) and not self.call_schedule:
            raise ValueError("call_schedule is required if callability flags are set")

        # Validate call_schedule entries
        if self.call_schedule:
            # Ensure the call_schedule is sorted by date ascending and valid data
            dates = []
            for entry in self.call_schedule:
                # Assuming CallScheduleEntry has: date: date, price: float, call_type: str
                if entry.price < 0:
                    raise ValueError("Call schedule price cannot be negative")
                if entry.date in dates:
                    raise ValueError("Duplicate call schedule date found: {}".format(entry.date))
                dates.append(entry.date)
            if dates != sorted(dates):
                raise ValueError("call_schedule must be sorted by date ascending")

            # # Ensure call_type matches bond flags if present
            # for entry in self.call_schedule:
            #     ct = entry.call_type.lower()
            #     if ct == 'american' and not self.is_american_call:
            #         raise ValueError("Call schedule entry type 'American' found but is_american_call is False")
            #     if ct == 'bermudan' and not self.is_bermudan_call:
            #         raise ValueError("Call schedule entry type 'Bermudan' found but is_bermudan_call is False")
            #     # European calls are allowed if neither american nor bermudan flags set? Allow?

        # Protection period and notice period must be non-negative if set (Field() enforces >=0)
        # call_premium must be non-negative if set

        return self


class CallableBondResponse(BondBaseResponse):
    coupon_rate: float
    coupon_frequency: FrequencyEnum

    call_schedule: List[CallScheduleEntry]

    call_protection_period_days: Optional[int] = None
    call_notice_period_days: Optional[int] = None
    call_premium: Optional[float] = None

    is_american_call: Optional[bool] = False
    is_bermudan_call: Optional[bool] = False
