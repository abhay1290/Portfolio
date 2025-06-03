from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String

from FixedIncome.src.model.bonds.BondBase import BondBase
from FixedIncome.src.model.enums.FrequencyEnum import FrequencyEnum


class FloatingRateBondModel(BondBase):
    __tablename__ = 'floating_rate_bonds'

    API_Path = "Floating_Rate_Bonds"

    bond_id = Column(Integer, ForeignKey('bonds.id'), primary_key=True)

    coupon_rate = Column(Float, nullable=False)
    coupon_frequency = Column(Enum(FrequencyEnum), nullable=False)

    reference_index = Column(String(50), nullable=True)
