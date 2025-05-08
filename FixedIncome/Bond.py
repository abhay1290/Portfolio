from datetime import datetime

from sqlalchemy import Column, Date, Enum, Float, Integer, String

from Database.database import Base
from FixedIncome.enums import CouponFrequencyEnum
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.DayCountConventionEnum import DayCountConventionEnum
from Identifier.SecurityIdentifier import SecurityIdentifier


class Bond(Base):
    __tablename__ = 'bonds'
    API_Path = "Bonds"

    # Define columns
    id = Column(Integer, primary_key=True, autoincrement=True)

    symbol = Column(String(50), nullable=False)
    face_value = Column(Float, nullable=False)
    coupon_rate = Column(Float, nullable=False)
    maturity_date = Column(Date, nullable=False)
    issue_date = Column(Date, nullable=False)
    market_price = Column(Float, nullable=False)
    bond_type = Column(Enum(BondTypeEnum), nullable=False)
    frequency = Column(Enum(CouponFrequencyEnum), nullable=False)

    day_count_convention = Column(Enum(DayCountConventionEnum), nullable=False)
    settlement_date = Column(Date, nullable=True)
    # asset_class = Column(Enum(AssetClassEnum), nullable=False, default=AssetClassEnum.FIXED_INCOME)

    credit_rating = Column(String(10), nullable=True)

    def __init__(self, symbol: SecurityIdentifier, face_value: float, coupon_rate: float, maturity_date: datetime,
                 issue_date: datetime,
                 market_price: float, bond_type: BondTypeEnum, frequency: CouponFrequencyEnum, credit_rating: str,
                 day_count_convention: DayCountConventionEnum, settlement_date: datetime):
        self.symbol = str(symbol)
        self.face_value = face_value
        self.coupon_rate = coupon_rate
        self.maturity_date = maturity_date
        self.issue_date = issue_date
        self.market_price = market_price
        self.bond_type = bond_type
        self.frequency = frequency
        self.credit_rating = credit_rating
        self.day_count_convention = day_count_convention
        self.settlement_date = settlement_date
