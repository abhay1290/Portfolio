from sqlalchemy import Column, Date, DateTime, Enum, Float, Integer, String, func

from fixed_income.src.database import Base
from fixed_income.src.model.enums import BondTypeEnum, BusinessDayConventionEnum, CalendarEnum, CompoundingEnum, \
    DayCountConventionEnum, FrequencyEnum
from fixed_income.src.model.enums.CurrencyEnum import CurrencyEnum


class BondBase(Base):
    __tablename__ = 'bonds'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Identifiers
    symbol = Column(String(50), nullable=True)
    bond_type = Column(Enum(BondTypeEnum), nullable=False, default=BondTypeEnum.ZERO_COUPON)
    currency = Column(Enum(CurrencyEnum), nullable=False, default=CurrencyEnum.USD)

    # Bond lifecycle dates
    issue_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)

    # Evaluation context
    evaluation_date = Column(Date, nullable=False)
    settlement_days = Column(Integer, nullable=False, default=2)
    calendar = Column(Enum(CalendarEnum), nullable=False, default=CalendarEnum.TARGET)
    business_day_convention = Column(Enum(BusinessDayConventionEnum), nullable=False,
                                     default=BusinessDayConventionEnum.FOLLOWING)

    # Financial values
    face_value = Column(Float, nullable=False)
    market_price = Column(Float, nullable=True)

    # Interest rate conventions
    day_count_convention = Column(Enum(DayCountConventionEnum), nullable=False,
                                  default=DayCountConventionEnum.ACTUAL_365_FIXED)
    compounding = Column(Enum(CompoundingEnum), nullable=False, default=CompoundingEnum.COMPOUNDED)
    frequency = Column(Enum(FrequencyEnum), nullable=False, default=FrequencyEnum.ANNUAL)
