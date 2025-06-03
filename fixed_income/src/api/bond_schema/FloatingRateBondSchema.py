from typing import Optional

from pydantic import Field, constr, model_validator

from fixed_income.src.api.bond_schema.BondBaseSchema import BondBaseRequest, BondBaseResponse
from fixed_income.src.model.enums import BondTypeEnum, FrequencyEnum


# Floating Rate Bond
class FloatingRateBondRequest(BondBaseRequest):
    coupon_rate: Optional[float] = Field(None, ge=0, description="Initial or current coupon rate (non-negative)")
    coupon_frequency: Optional[FrequencyEnum] = Field(None, description="Coupon payment frequency (e.g., Quarterly)")

    reference_index: Optional[constr(max_length=50)] = Field(
        None, description="Name of reference rate index (e.g., LIBOR, SOFR) used to reset coupons"
    )

    @model_validator(mode='after')
    def validate_floating_bond(self):
        if self.bond_type != BondTypeEnum.FLOATING:
            raise ValueError("bond_type must be FLOATING for this request")

        if self.coupon_rate is None:
            raise ValueError("coupon_rate is required for floating rate bonds")

        if self.coupon_frequency is None:
            raise ValueError("coupon_frequency is required for floating rate bonds")

        return self


class FloatingRateBondResponse(BondBaseResponse):
    coupon_rate: float
    coupon_frequency: FrequencyEnum

    reference_index: str
