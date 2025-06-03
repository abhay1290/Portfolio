from pydantic import BaseModel, ConfigDict

from Currency.CurrencyEnum import CurrencyEnum
from Identifier.AssetClassEnum import AssetClassEnum
from Identifier.TaxTypeEnum import TaxTypeEnum
from Identifier.WeightingMethodologyEnum import WeightingMethodologyEnum


class PortfolioBase(BaseModel):
    symbol: str
    currency: CurrencyEnum
    asset_class: AssetClassEnum
    tax_type: TaxTypeEnum
    weighting_methodology: WeightingMethodologyEnum


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioResponse(PortfolioBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
