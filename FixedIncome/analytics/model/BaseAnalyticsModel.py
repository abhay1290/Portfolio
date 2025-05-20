from sqlalchemy import Column, Date, Enum, Float, ForeignKey, Integer, JSON, UniqueConstraint

from FixedIncome.database import Base
from FixedIncome.enums.BondTypeEnum import BondTypeEnum


class BondAnalyticsModel(Base):
    __tablename__ = "bond_analytics"

    id = Column(Integer, primary_key=True)
    bond_id = Column(Integer, ForeignKey("bonds.id"), index=True)
    analytics_date = Column(Date)
    bond_type = Column(Enum(BondTypeEnum))

    clean_price = Column(Float)
    dirty_price = Column(Float)
    accrued_interest = Column(Float)

    ytm = Column(Float)
    ytw = Column(Float)

    duration_mod = Column(Float)
    duration_mac = Column(Float)
    duration_simple = Column(Float)

    convexity = Column(Float)
    dv01 = Column(Float)

    summary = Column(JSON)

    __table_args__ = (UniqueConstraint("bond_id", "analytics_date"),)
