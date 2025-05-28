from sqlalchemy import Column, Enum, Integer, String

from Currency.CurrencyEnum import CurrencyEnum
from Identifier.AssetClassEnum import AssetClassEnum
from Identifier.TaxTypeEnum import TaxTypeEnum
from Identifier.WeightingMethodologyEnum import WeightingMethodologyEnum
from Portfolios.database import Base


class Portfolio(Base):
    __tablename__ = 'portfolio'
    API_Path = "Portfolio"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(100), nullable=False)

    currency = Column(Enum(CurrencyEnum), nullable=False)
    asset_class = Column(Enum(AssetClassEnum), nullable=False)
    tax_type = Column(Enum(TaxTypeEnum), nullable=False)
    weighting_methodology = Column(Enum(WeightingMethodologyEnum), nullable=False)

    def __init__(self, symbol, currency: CurrencyEnum, asset_class: AssetClassEnum,
                 tax_type: TaxTypeEnum, weighting_methodology: WeightingMethodologyEnum):
        self.symbol = symbol
        self.currency = currency
        self.asset_class = asset_class
        self.tax_type = tax_type
        self.weighting_methodology = weighting_methodology

        # If no constituents provided, initialize as an empty list
        self.constituentIds = []
