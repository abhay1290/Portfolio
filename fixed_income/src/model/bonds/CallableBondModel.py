from sqlalchemy import Boolean, Column, Enum, Float, ForeignKey, Integer, JSON

from fixed_income.src.model.bonds import BondBase
from fixed_income.src.model.enums import FrequencyEnum


class CallableBondModel(BondBase):
    __tablename__ = 'callable_bonds'

    API_Path = "Callable_Bonds"

    bond_id = Column(Integer, ForeignKey('bonds.id'), primary_key=True)

    coupon_rate = Column(Float, nullable=False)
    coupon_frequency = Column(Enum(FrequencyEnum), nullable=False)

    # Call schedule stored as JSON: list of dicts with date, price, call type (American/European/Bermudan)
    call_schedule = Column(JSON, nullable=True)

    # Call protection period: no call allowed before this many days/months from issue
    call_protection_period_days = Column(Integer, nullable=True)

    # Call notice period (days before call exercise date)
    call_notice_period_days = Column(Integer, nullable=True)

    # Optional call premiums or fees expressed as percent or fixed amount
    call_premium = Column(Float, nullable=True)

    # Flags to indicate type of callability
    is_american_call = Column(Boolean, nullable=True)
    is_bermudan_call = Column(Boolean, nullable=True)
