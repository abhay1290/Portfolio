from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, JSON

from FixedIncome.enums.CouponFrequencyEnum import CouponFrequencyEnum
from FixedIncome.model.BondBase import BondBase


class SinkingFundBondModel(BondBase):
    __tablename__ = 'sinking_fund_bonds'

    API_Path = "Sinking_Fund_Bonds"

    bond_id = Column(Integer, ForeignKey('bonds.id'), primary_key=True)

    coupon_rate = Column(Float, nullable=True)
    coupon_frequency = Column(Enum(CouponFrequencyEnum), nullable=True)
    coupon_schedule = Column(JSON, nullable=True)

    notionals_schedule = Column(JSON, nullable=True)
