from pydantic import Field, model_validator

from FixedIncome.api.bond_schema.BondBaseSchema import BondBaseRequest, BondBaseResponse
from FixedIncome.enums.BondTypeEnum import BondTypeEnum


class ZeroCouponBondRequest(BondBaseRequest):
    accrues_interest_flag: bool = Field(default=False,
                                        description="Whether accrued interest is applicable for the zero coupon bond")

    @model_validator(mode='after')
    def validate_zero_coupon_bond(self):
        if self.bond_type != BondTypeEnum.ZERO_COUPON:
            raise ValueError("bond_type must be ZERO_COUPON for this request")
        return self


class ZeroCouponBondResponse(BondBaseResponse):
    accrues_interest_flag: bool
