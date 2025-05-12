from datetime import date

from pydantic import BaseModel, Field


class CouponScheduleEntry(BaseModel):
    coupon_date: date
    coupon_value: float = Field(..., ge=0, description="Coupon payment amount (must be non-negative)")
