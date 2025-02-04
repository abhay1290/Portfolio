from datetime import datetime

from sqlalchemy import Column, Date, Float, Integer, String, Enum

from Database.database import Base
from FixedIncome.BondTypeEnum import BondTypeEnum
from FixedIncome.DayCountConventionEnum import DayCountConventionEnum
from Identifier.SecurityIdentifier import SecurityIdentifier


class Bond(Base):
    __tablename__ = 'bonds'
    API_Path = "Bonds"

    # Define columns
    id = Column(Integer, primary_key=True, autoincrement=True)

    symbol = Column(String(10000), nullable=False)
    face_value = Column(Float, nullable=False)
    coupon_rate = Column(Float, nullable=False)
    maturity_date = Column(Date, nullable=False)
    issue_date = Column(Date, nullable=False)
    market_price = Column(Float, nullable=False)
    bond_type = Column(Enum(BondTypeEnum), nullable=False)
    frequency = Column(Float, nullable=False)
    day_count_convention = Column(Enum(DayCountConventionEnum), nullable=False)
    settlement_date = Column(Date, nullable=True)

    # issuer =
    # issuer_type =
    credit_rating = Column(String(10), nullable=True)



    def __init__(self, symbol: SecurityIdentifier, face_value: float, coupon_rate: float, maturity_date: datetime, issue_date: datetime,
                 market_price: float, bond_type: BondTypeEnum, frequency: float, credit_rating: str,
                 day_count_convention: DayCountConventionEnum, settlement_date: str):

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
        self.settlement_date = datetime.strptime(settlement_date, "%Y-%m-%d")
