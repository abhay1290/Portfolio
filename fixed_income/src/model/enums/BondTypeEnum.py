from enum import Enum


class BondTypeEnum(str, Enum):
    ZERO_COUPON = "ZERO_COUPON"
    FIXED_COUPON = "FIXED_COUPON"
    FLOATING = "FLOATING"
    CALLABLE = "CALLABLE"
    PUTABLE = "PUTABLE"
    SINKING_FUND = "SINKING_FUND"
