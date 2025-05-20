from sqlalchemy import Column, Date, Enum, Float, ForeignKey, Integer

from FixedIncome.enums.BusinessDayConventionEnum import BusinessDayConventionEnum
from FixedIncome.enums.CalenderEnum import CalendarEnum
from FixedIncome.enums.FrequencyEnum import FrequencyEnum
from FixedIncome.model.BondBase import BondBase


class FixedRateBondModel(BondBase):
    __tablename__ = 'fixed_rate_bonds'

    API_Path = "Fixed_Rate_Bonds"

    bond_id = Column(Integer, ForeignKey('bonds.id'), primary_key=True)

    coupon_rate = Column(Float, nullable=False)
    coupon_frequency = Column(Enum(FrequencyEnum), nullable=False)

    # Redemption info
    redemption_value = Column(Float, nullable=False, default=100.0)  # % of face value at maturity or call
    redemption_date = Column(Date, nullable=True)  # If different from maturity

    # Business day adjustment for coupons and redemption (following, preceding, modified following)
    business_day_convention = Column(Enum(BusinessDayConventionEnum), nullable=False)

    # Optional ex-coupon days info
    ex_coupon_days = Column(Integer, nullable=True)
    ex_coupon_calendar = Column(Enum(CalendarEnum), nullable=True)
