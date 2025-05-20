from sqlalchemy import Column, Date, Enum, Float, ForeignKey, Integer, JSON

from FixedIncome.enums.FrequencyEnum import FrequencyEnum
from FixedIncome.enums.SinkingFundTypeEnum import SinkingFundTypeEnum
from FixedIncome.model.BondBase import BondBase


class SinkingFundBondModel(BondBase):
    __tablename__ = 'sinking_fund_bonds'

    API_Path = "Sinking_Fund_Bonds"

    bond_id = Column(Integer, ForeignKey('bonds.id'), primary_key=True)

    coupon_rate = Column(Float, nullable=False)
    coupon_frequency = Column(Enum(FrequencyEnum), nullable=False)

    # Sinking fund schedule as JSON: list of amortization dates & amounts or percentages
    sinking_fund_schedule = Column(JSON, nullable=True)

    # Rules for mandatory sinking fund calls: e.g. fixed amount, percentage, optional early redemption
    sinking_fund_type = Column(Enum(SinkingFundTypeEnum), nullable=True)

    # Date from which sinking fund schedule starts, if different from issue_date
    sinking_fund_start_date = Column(Date, nullable=True)
