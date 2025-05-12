from pydantic import model_validator

from FixedIncome.api.bond_schema.BondBaseSchema import BondBaseRequest, BondBaseResponse
from FixedIncome.enums.BondTypeEnum import BondTypeEnum


class ZeroCouponBondRequest(BondBaseRequest):

    @model_validator(mode='after')
    def validate_zero_coupon_bond(self):
        if self.bond_type != BondTypeEnum.ZERO_COUPON:
            raise ValueError("bond_type must be ZERO_COUPON for this request")
        return self


class ZeroCouponBondResponse(BondBaseResponse):
    pass
