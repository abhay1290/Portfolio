from sqlalchemy import Column, Enum, Float, JSON

from FixedIncome.enums.CouponFrequencyEnum import CouponFrequencyEnum
from FixedIncome.model.BondBase import BondBase


class CallableBondModel(BondBase):
    __tablename__ = 'callable_bonds'

    coupon_rate = Column(Float, nullable=True)
    coupon_frequency = Column(Enum(CouponFrequencyEnum), nullable=True)
    coupon_schedule = Column(JSON, nullable=True)

    call_schedule = Column(JSON, nullable=True)
