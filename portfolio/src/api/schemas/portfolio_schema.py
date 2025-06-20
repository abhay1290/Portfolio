from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from portfolio.src.api.schemas.constituent_schema import PortfolioBondRequest, PortfolioBondResponse, \
    PortfolioEquityRequest, PortfolioEquityResponse
from portfolio.src.model.enums import AssetClassEnum, BusinessDayConventionEnum, CalendarEnum, CurrencyEnum, \
    RiskLevelEnum, VersionOperationTypeEnum, WeightingMethodologyEnum
from portfolio.src.model.enums.PortfolioStatusEnum import PortfolioStatusEnum
from portfolio.src.model.enums.PortfolioTypeEnum import PortfolioTypeEnum
from portfolio.src.model.enums.RebalanceFrequencyEnum import RebalanceFrequencyEnum


class PortfolioBase(BaseModel):
    # Primary identifiers
    symbol: str = Field(..., max_length=100, description="Unique portfolio symbol/ticker")
    name: str = Field(..., max_length=200, description="Portfolio name")
    description: Optional[str] = Field(None, description="Detailed description of the portfolio")

    # Portfolio classification
    portfolio_type: PortfolioTypeEnum = Field(default=PortfolioTypeEnum.QUANTITATIVE,
                                              description="The type of the portfolio.")
    base_currency: CurrencyEnum = Field(default=CurrencyEnum.USD,
                                        description="The base currency for reporting and valuation.")
    asset_class: AssetClassEnum = Field(default=AssetClassEnum.EQUITY,
                                        description="The primary asset class of the portfolio.")

    # Portfolio lifecycle
    inception_date: date = Field(..., description="The date the portfolio was launched.")
    termination_date: Optional[date] = Field(None, description="The date the portfolio was terminated, if applicable.")
    status: PortfolioStatusEnum = Field(default=PortfolioStatusEnum.ACTIVE,
                                        description="The current operational status of the portfolio.")

    # Portfolio methodology and strategy
    weighting_methodology: WeightingMethodologyEnum = Field(...,
                                                            description="The method used to determine constituent weights.")
    rebalance_frequency: RebalanceFrequencyEnum = Field(..., description="How often the portfolio is rebalanced.")
    benchmark_symbol: Optional[str] = Field(None, max_length=100,
                                            description="The symbol of the benchmark index, e.g., 'SPX'.")
    strategy_description: Optional[str] = Field(None, description="A detailed description of the investment strategy.")

    # Financial metrics and investment terms
    minimum_investment: Optional[Decimal] = Field(None, ge=0, decimal_places=2,
                                                  description="The minimum investment amount required.")

    # Risk and constraints
    risk_level: Optional[RiskLevelEnum] = Field(None, description="The target risk level of the portfolio.")
    max_individual_weight: Optional[Decimal] = Field(None, ge=0, le=1, decimal_places=4,
                                                     description="Maximum weight for any single constituent.")
    min_individual_weight: Optional[Decimal] = Field(None, ge=0, le=1, decimal_places=4,
                                                     description="Minimum weight for any single constituent.")
    max_sector_weight: Optional[Decimal] = Field(None, ge=0, le=1, decimal_places=4,
                                                 description="Maximum weight for any single sector.")
    max_country_weight: Optional[Decimal] = Field(None, ge=0, le=1, decimal_places=4,
                                                  description="Maximum weight for any single country.")
    cash_target_percentage: Optional[Decimal] = Field(None, ge=0, le=1, decimal_places=4,
                                                      description="Target cash allocation percentage.")

    # Evaluation and calculation context
    calendar: CalendarEnum = Field(default=CalendarEnum.TARGET,
                                   description="The calendar used for business day calculations.")
    business_day_convention: BusinessDayConventionEnum = Field(default=BusinessDayConventionEnum.FOLLOWING,
                                                               description="Convention for adjusting non-business days.")
    last_rebalance_date: Optional[date] = Field(None, description="The date of the last rebalance.")
    next_rebalance_date: Optional[date] = Field(None, description="The scheduled date for the next rebalance.")

    # Fees and expenses
    management_fee: Optional[Decimal] = Field(None, ge=0, decimal_places=4,
                                              description="Annual management fee percentage.")
    performance_fee: Optional[Decimal] = Field(None, ge=0, decimal_places=4, description="Performance fee percentage.")
    expense_ratio: Optional[Decimal] = Field(None, ge=0, decimal_places=4, description="Total annual expense ratio.")

    # Operational fields
    is_active: bool = Field(default=True, description="Whether the portfolio is actively managed.")
    is_locked: bool = Field(default=False, description="Whether the portfolio is locked from further changes.")
    allow_fractional_shares: bool = Field(default=True, description="If trading can result in fractional shares.")
    auto_rebalance_enabled: bool = Field(default=False,
                                         description="If the portfolio should be automatically rebalanced.")

    # Metadata and configuration
    custom_fields: Optional[Dict[str, Any]] = Field(default_factory=dict,
                                                    description="Custom key-value pairs for additional data.")
    compliance_rules: Optional[List[Any]] = Field(default_factory=list,
                                                  description="A list of compliance rules applied.")
    tags: Optional[List[str]] = Field(default_factory=list, description="A list of tags for categorization.")

    # Manager/Administrator information
    portfolio_manager: Optional[str] = Field(None, max_length=200, description="Name of the portfolio manager.")
    administrator: Optional[str] = Field(None, max_length=200, description="Name of the portfolio administrator.")
    custodian: Optional[str] = Field(None, max_length=200, description="Name of the custodian.")


class PortfolioRequest(PortfolioBase):
    """Schema for creating or updating a portfolio."""
    equity_ids: List[PortfolioEquityRequest] = Field(default_factory=list,
                                                     description="List of equities to include in the portfolio.")
    bond_ids: List[PortfolioBondRequest] = Field(default_factory=list,
                                                 description="List of bonds to include in the portfolio.")


class PortfolioResponse(PortfolioBase):
    """Schema for a single portfolio response, including all database-generated fields."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Version tracking fields
    version: int
    version_hash: Optional[str] = Field(None, max_length=64)
    current_version_id: Optional[int] = None

    # Financial metrics (often calculated)
    total_market_value: Optional[Decimal] = Field(None, decimal_places=2)
    nav_per_share: Optional[Decimal] = Field(None, decimal_places=6)
    total_shares_outstanding: Optional[Decimal] = Field(None, decimal_places=0)
    last_nav_calculation_date: Optional[date] = None

    # Related constituents
    equities: List[PortfolioEquityResponse] = Field(default_factory=list)
    bonds: List[PortfolioBondResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PortfolioVersionResponse(BaseModel):
    """Schema for a single version record of a portfolio."""
    id: int
    portfolio_id: int
    version_id: int
    state_hash: str

    # State data
    portfolio_state: Dict[str, Any]
    constituents_state: List[Dict[str, Any]]

    # Metadata
    operation_type: VersionOperationTypeEnum
    change_reason: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: datetime
    previous_version_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class VersionComparisonResponse(BaseModel):
    pass


class PortfolioSummaryResponse(BaseModel):
    """A summarized view of a portfolio for list displays."""
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
    last_rebalance_date: Optional[date]
    next_rebalance_date: Optional[date]

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
    portfolio_id: int
    symbol: str
    inception_to_date_return: Optional[float] = None
    year_to_date_return: Optional[float] = None
    one_year_return: Optional[float] = None
    three_year_annualized: Optional[float] = None
    five_year_annualized: Optional[float] = None
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    benchmark_symbol: Optional[str] = None
    benchmark_returns: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)
