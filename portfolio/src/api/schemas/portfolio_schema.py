from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from portfolio.src.api.schemas.constituent_schema import PortfolioBondRequest, PortfolioBondResponse, \
    PortfolioEquityRequest, \
    PortfolioEquityResponse
from portfolio.src.model.enums import AssetClassEnum, BusinessDayConventionEnum, CalendarEnum, CurrencyEnum, \
    WeightingMethodologyEnum
from portfolio.src.model.enums.PortfolioStatusEnum import PortfolioStatusEnum
from portfolio.src.model.enums.PortfolioTypeEnum import PortfolioTypeEnum
from portfolio.src.model.enums.RebalanceFrequencyEnum import RebalanceFrequencyEnum


class PortfolioBase(BaseModel):
    # Primary identifiers
    symbol: str = Field(..., max_length=100, description="PORTF1")
    name: str = Field(..., max_length=200, description="Global Equity Portfolio")
    description: Optional[str] = Field(None, description="Diversified global equity portfolio")
    inception_date: date

    # Portfolio classification
    portfolio_type: Annotated[PortfolioTypeEnum, Field(default=PortfolioTypeEnum.QUANTITATIVE,
                                                       description="Portfolio type")]
    status: Annotated[PortfolioStatusEnum, Field(default=PortfolioStatusEnum.ACTIVE,
                                                 description="Status for processing")]
    base_currency: Annotated[CurrencyEnum, Field(default=CurrencyEnum.USD,
                                                 description="Primary currency in which the portfolio is denominated")]
    asset_class: Annotated[AssetClassEnum, Field(default=AssetClassEnum.EQUITY,
                                                 description="asset classes of the underlying constituents")]

    # Portfolio methodology and strategy
    weighting_methodology: WeightingMethodologyEnum
    rebalance_frequency: RebalanceFrequencyEnum
    benchmark_symbol: Optional[str] = Field(None, max_length=100, description="SPX")
    strategy_description: Optional[str] = Field(None)

    # Evaluation and calculation context
    calendar: Annotated[CalendarEnum, Field(default=CalendarEnum.TARGET,
                                            description="Calendar used for business day calculations")]
    business_day_convention: Annotated[BusinessDayConventionEnum, Field(default=BusinessDayConventionEnum.FOLLOWING,
                                                                        description="Business day convention for date adjustments")]

    allow_fractional_shares: Optional[bool] = Field(default=True)
    auto_rebalance_enabled: Optional[bool] = Field(default=True)

    equity_ids: Annotated[List[PortfolioEquityRequest], Field(default_factory=list,
                                                              description="List of equities to add")]
    bond_ids: Annotated[List[PortfolioBondRequest], Field(default_factory=list,
                                                          description="List of bonds to add")]


class PortfolioRequest(PortfolioBase):
    pass


class PortfolioResponse(PortfolioBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    version: int
    total_market_value: Annotated[Optional[Decimal], Field(None, decimal_places=2)]
    equities: List[PortfolioEquityResponse] = Field(default_factory=list)
    bonds: List[PortfolioBondResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PortfolioSummaryResponse(BaseModel):
    id: int
    symbol: str
    name: str
    portfolio_type: str
    base_currency: str
    asset_class: str
    status: str
    total_market_value: Optional[Decimal]
    nav_per_share: Optional[Decimal]
    equity_count: int
    bond_count: int
    last_updated: Optional[datetime]
    last_rebalance_date = Optional[datetime]
    next_rebalance_date = Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class PortfolioConstituentSummary(BaseModel):
    equity_count: int
    bond_count: int
    total_constituents: int
    total_market_value: Optional[Decimal]
    total_weight: Optional[Decimal]
    last_updated: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class PortfolioPerformanceResponse(BaseModel):
    portfolio_id: str
    symbol: str
    inception_to_date_return: Optional[float] = None
    year_to_date_return: Optional[float] = None
    one_year_return: Optional[float] = None
    three_year_annualized: Optional[float] = None
    five_year_annualized: Optional[float] = None
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    benchmark_symbol: str
    benchmark_returns: Optional[float] = None
    last_updated: datetime = datetime.now()

    model_config = ConfigDict(from_attributes=True)
