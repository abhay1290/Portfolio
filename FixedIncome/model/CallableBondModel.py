from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, JSON

from FixedIncome.enums.CouponFrequencyEnum import CouponFrequencyEnum
from FixedIncome.model.BondBase import BondBase


class CallableBondModel(BondBase):
    __tablename__ = 'callable_bonds'

    API_Path = "Callable_Bonds"

    bond_id = Column(Integer, ForeignKey('bonds.id'), primary_key=True)

    coupon_rate = Column(Float, nullable=True)
    coupon_frequency = Column(Enum(CouponFrequencyEnum), nullable=True)
    coupon_schedule = Column(JSON, nullable=True)

    call_schedule = Column(JSON, nullable=True)
