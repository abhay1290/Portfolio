from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, JSON

from FixedIncome.enums.CouponFrequencyEnum import CouponFrequencyEnum
from FixedIncome.model.BondBase import BondBase


class PutableBondModel(BondBase):
    __tablename__ = 'putable_bonds'

    API_Path = "Putable_Bonds"

    bond_id = Column(Integer, ForeignKey('bonds.id'), primary_key=True)

    coupon_rate = Column(Float, nullable=True)
    coupon_frequency = Column(Enum(CouponFrequencyEnum), nullable=True)
    coupon_schedule = Column(JSON, nullable=True)

    put_schedule = Column(JSON, nullable=True)
