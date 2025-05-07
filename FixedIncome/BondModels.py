from sqlalchemy import Column, Date, Enum, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSON

from Database.database import Base
from FixedIncome.BondTypeEnum import BondTypeEnum
from FixedIncome.CouponFrequencyEnum import CouponFrequencyEnum
from FixedIncome.DayCountConventionEnum import DayCountConventionEnum


class BondBase(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=True)
    face_value = Column(Float, nullable=True)
    maturity_date = Column(Date, nullable=True)
    issue_date = Column(Date, nullable=True)
    market_price = Column(Float, nullable=True)
    bond_type = Column(Enum(BondTypeEnum), nullable=True)
    settlement_date = Column(Date, nullable=True)
    credit_rating = Column(String(10), nullable=True)


class ZeroCouponBondModel(BondBase):
    __tablename__ = 'zero_coupon_bonds'
    pass


class FixedRateBondModel(BondBase):
    __tablename__ = 'fixed_rate_bonds'
    coupon_rate = Column(Float, nullable=True)
    frequency = Column(Enum(CouponFrequencyEnum), nullable=True)
    coupon_schedule = Column(JSON, nullable=True)

    day_count_convention = Column(Enum(DayCountConventionEnum), nullable=True)


class CallableBondModel(BondBase):
    __tablename__ = 'callable_bonds'
    coupon_rate = Column(Float, nullable=True)
    frequency = Column(Enum(CouponFrequencyEnum), nullable=True)
    coupon_schedule = Column(JSON, nullable=True)

    day_count_convention = Column(Enum(DayCountConventionEnum), nullable=True)

    call_schedule = Column(JSON, nullable=True)


class PutableBondModel(BondBase):
    __tablename__ = 'putable_bonds'
    coupon_rate = Column(Float, nullable=True)
    frequency = Column(Enum(CouponFrequencyEnum), nullable=True)
    coupon_schedule = Column(JSON, nullable=True)

    day_count_convention = Column(Enum(DayCountConventionEnum), nullable=True)

    put_schedule = Column(JSON, nullable=True)


class FloatingRateBondModel(BondBase):
    __tablename__ = 'floating_rate_bonds'
    coupon_rate = Column(Float, nullable=True)
    frequency = Column(Enum(CouponFrequencyEnum), nullable=True)
    coupon_schedule = Column(JSON, nullable=True)

    day_count_convention = Column(Enum(DayCountConventionEnum), nullable=True)

    reference_index = Column(String(50), nullable=True)


class BondAnalyticsResults(Base):
    __tablename__ = 'bond_analytics_results'

    as_of_date = Column(Date, nullable=True)

    id = Column(Integer, primary_key=True, autoincrement=True)
    bond_id = Column(Integer, nullable=False)
    bond_type = Column(Enum(BondTypeEnum), nullable=False)

    clean_price = Column(Float, nullable=True)
    dirty_price = Column(Float, nullable=True)
    accrued_interest = Column(Float, nullable=True)

    yield_to_maturity = Column(Float, nullable=True)
    yield_to_worst = Column(Float, nullable=True)

    modified_duration = Column(Float, nullable=True)
    macaulay_duration = Column(Float, nullable=True)
    simple_duration = Column(Float, nullable=True)
    convexity = Column(Float, nullable=True)
    dv01 = Column(Float, nullable=True)
