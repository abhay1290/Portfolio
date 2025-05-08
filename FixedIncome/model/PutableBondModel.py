from sqlalchemy import Column, Enum, Float, JSON

from FixedIncome.enums.CouponFrequencyEnum import CouponFrequencyEnum
from FixedIncome.model.BondBase import BondBase


class PutableBondModel(BondBase):
    __tablename__ = 'putable_bonds'

    coupon_rate = Column(Float, nullable=True)
    frequency = Column(Enum(CouponFrequencyEnum), nullable=True)
    coupon_schedule = Column(JSON, nullable=True)

    put_schedule = Column(JSON, nullable=True)
