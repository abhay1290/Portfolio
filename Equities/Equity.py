from sqlalchemy import Column, Integer, String, Float, Enum
from sqlalchemy.orm import backref, relationship

from Currency.CurrencyEnum import CurrencyEnum
from Identifier.AssetClassEnum import AssetClassEnum
from Identifier.SecurityIdentifier import SecurityIdentifier

from Database.database2 import Base

class Equity(Base):
    __tablename__ = 'equity'

    id = Column(Integer, primary_key=True, autoincrement=True)

    symbol = Column(String(10000), nullable=False, unique=True)
    #asset_class = Column(Enum(AssetClassEnum), nullable=False)
    company_name = Column(String(100), nullable=False)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)

    price = Column(Float, nullable=False)
    currency = Column(Enum(CurrencyEnum), nullable=False)
    volume = Column(Integer, nullable=False)

    # One-to-many relationship to CorporateAction
    corporate_actions = relationship(
        'CorporateAction',
        backref=backref('equity', lazy='joined'),
        cascade='all, delete-orphan'
    )

    def __init__(self, symbol: SecurityIdentifier, company_name: str, price: float,
                 volume: float, currency: CurrencyEnum, sector=None, industry=None):

        self.symbol = str(symbol)
        self.company_name = company_name
        self.price = price
        self.volume = volume
        self.currency = currency
        self.sector = sector
        self.industry = industry

    def __str__(self):
        return f"{self.company_name} ({self.symbol}): {self.currency} {self.price} - Volume: {self.volume}"

    def get_market_cap(self, shares_outstanding):
        return self.price * shares_outstanding


