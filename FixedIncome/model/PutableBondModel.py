from sqlalchemy import Boolean, Column, Enum, Float, ForeignKey, Integer, JSON

from FixedIncome.enums.FrequencyEnum import FrequencyEnum
from FixedIncome.model.BondBase import BondBase


class PutableBondModel(BondBase):
    __tablename__ = 'putable_bonds'

    API_Path = "Putable_Bonds"

    bond_id = Column(Integer, ForeignKey('bonds.id'), primary_key=True)

    coupon_rate = Column(Float, nullable=False)
    coupon_frequency = Column(Enum(FrequencyEnum), nullable=False)

    # Put schedule stored as JSON: list of dicts with date, price, put type (American/European/Bermudan)
    put_schedule = Column(JSON, nullable=True)

    # Put protection period: no put allowed before this many days/months from issue
    put_protection_period_days = Column(Integer, nullable=True)

    # Put notice period (days before put exercise date)
    put_notice_period_days = Column(Integer, nullable=True)

    # Optional put premiums or fees expressed as percent or fixed amount
    put_premium = Column(Float, nullable=True)

    # Flags to indicate type of callability
    is_american_put = Column(Boolean, nullable=True)
    is_bermudan_put = Column(Boolean, nullable=True)
