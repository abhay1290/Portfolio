from typing import List, Optional

from pydantic import Field, model_validator

from fixed_income.src.api.bond_schema.BondBaseSchema import BondBaseRequest, BondBaseResponse
from fixed_income.src.api.schedule_schema.PutScheduleSchema import PutScheduleEntry
from fixed_income.src.model.enums import BondTypeEnum, FrequencyEnum


# Putable Bond
class PutableBondRequest(BondBaseRequest):
    coupon_rate: Optional[float] = Field(None, ge=0, description="Annual coupon rate (non-negative)")
    coupon_frequency: Optional[FrequencyEnum] = Field(None, description="Coupon payment frequency")

    put_schedule: Optional[List[PutScheduleEntry]] = Field(None,
                                                           description="Put schedule with date, price, and put type")

    put_protection_period_days: Optional[int] = Field(None, ge=0,
                                                      description="Days before put is allowed after issuance")
    put_notice_period_days: Optional[int] = Field(None, ge=0, description="Days notice required to exercise put")
    put_premium: Optional[float] = Field(None, ge=0, description="Put premium or fee as percent or amount")

    is_american_put: Optional[bool] = Field(None, description="True if American-style put")
    is_bermudan_put: Optional[bool] = Field(None, description="True if Bermudan-style put")

    @model_validator(mode='after')
    def validate_putable_bond(self):
        # bond_type must be putable
        if self.bond_type != BondTypeEnum.PUTABLE:
            raise ValueError("bond_type must be PUTABLE for this request")

        # coupon_rate is required for putable bonds
        if self.coupon_rate is None:
            raise ValueError("coupon_rate is required for putable bonds")

        # coupon_frequency is required for putable bonds
        if self.coupon_frequency is None:
            raise ValueError("coupon_frequency is required for putable bonds")

        # Validate put_schedule presence if any putability flags are true
        if (self.is_american_put or self.is_bermudan_put) and not self.put_schedule:
            raise ValueError("put_schedule is required if putability flags are set")

        # Validate put_schedule entries
        if self.put_schedule:
            # Ensure the put_schedule is sorted by date ascending and valid data
            dates = []
            for entry in self.put_schedule:
                # Assuming PutScheduleEntry has: date: date, price: float, put_type: str
                if entry.price < 0:
                    raise ValueError("Put schedule price cannot be negative")
                if entry.date in dates:
                    raise ValueError("Duplicate put schedule date found: {}".format(entry.date))
                dates.append(entry.date)
            if dates != sorted(dates):
                raise ValueError("put_schedule must be sorted by date ascending")

        return self


class PutableBondResponse(BondBaseResponse):
    coupon_rate: float
    coupon_frequency: FrequencyEnum

    put_schedule: List[PutScheduleEntry]

    put_protection_period_days: Optional[int]
    put_notice_period_days: Optional[int]
    put_premium: Optional[float]

    is_american_put: Optional[bool]
    is_bermudan_put: Optional[bool]
