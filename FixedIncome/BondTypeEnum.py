from enum import Enum

class BondTypeEnum(Enum):
    ZERO_COUPON = "Zero Coupon"
    FIXED_COUPON = "Fixed Coupon"
    CALLABLE = "Callable"
    PUTABLE = "Putable"

