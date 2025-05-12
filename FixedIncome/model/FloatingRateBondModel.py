from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, JSON, String

from FixedIncome.enums.CouponFrequencyEnum import CouponFrequencyEnum
from FixedIncome.model.BondBase import BondBase


class FloatingRateBondModel(BondBase):
    __tablename__ = 'floating_rate_bonds'

    API_Path = "Floating_Rate_Bonds"

    bond_id = Column(Integer, ForeignKey('bonds.id'), primary_key=True)

    coupon_rate = Column(Float, nullable=True)
    coupon_frequency = Column(Enum(CouponFrequencyEnum), nullable=True)
    coupon_schedule = Column(JSON, nullable=True)

    reference_index = Column(String(50), nullable=True)
