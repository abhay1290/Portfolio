from sqlalchemy import Column, Date, Enum, Float, Integer, String

from Currency.CurrencyEnum import CurrencyEnum
from Database.database import Base
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.DayCountConventionEnum import DayCountConventionEnum


class BondBase(Base):
    # __abstract__ = True

    __tablename__ = 'bonds'

    id = Column(Integer, primary_key=True, autoincrement=True)

    symbol = Column(String(50), nullable=True)
    bond_type = Column(Enum(BondTypeEnum), nullable=True)
    currency = Column(Enum(CurrencyEnum), nullable=True)

    issue_date = Column(Date, nullable=True)
    maturity_date = Column(Date, nullable=True)
    settlement_date = Column(Date, nullable=True)
    settlement_days = Column(Integer, nullable=True)

    credit_rating = Column(String(10), nullable=True)

    face_value = Column(Float, nullable=True)
    market_price = Column(Float, nullable=True)

    day_count_convention = Column(Enum(DayCountConventionEnum), nullable=True)
