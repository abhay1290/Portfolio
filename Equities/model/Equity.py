from sqlalchemy import Column, DateTime, Enum, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB

from Currency.CurrencyEnum import CurrencyEnum
from Equities.database import Base


class Equity(Base):
    __tablename__ = 'equity'
    API_Path = "Equity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # index_memberships = Column(Text, nullable=True)  # JSON array of index names

    symbol = Column(String(10000), nullable=False)

    currency = Column(Enum(CurrencyEnum), nullable=False)
    market_price = Column(Float, nullable=True)
    shares_outstanding = Column(Integer, nullable=True)
    float_shares = Column(Integer, nullable=True)
    market_cap = Column(Float, nullable=True)

    # Store corporate action IDs as JSONB array
    corporate_action_ids = Column(JSONB, nullable=True, default=list)

    # Exchange and Trading Information
    # primary_exchange = Column(Enum(ExchangeEnum), nullable=False)
    # secondary_exchanges = Column(Text, nullable=True)  # JSON array of secondary exchanges
    #
    # share_class = Column(Enum(ShareClassEnum), nullable=False, default=ShareClassEnum.COMMON)
    # trading_status = Column(Enum(TradingStatusEnum), nullable=False, default=TradingStatusEnum.ACTIVE)

    # # Valuation Metrics
    # shares_outstanding = Column(Integer, nullable=True)
    # float_shares = Column(Integer, nullable=True)  # Publicly tradeable shares
    # market_cap = Column(Float, nullable=True)
    # market_cap_category = Column(Enum(MarketCapEnum), nullable=True)
    # enterprise_value = Column(Float, nullable=True)
    # book_value_per_share = Column(Float, nullable=True)
    # price_to_book = Column(Float, nullable=True)
    # price_to_earnings = Column(Float, nullable=True)
    # price_to_sales = Column(Float, nullable=True)
    # price_to_cash_flow = Column(Float, nullable=True)

    # # Financial Health Indicators
    # beta = Column(Float, nullable=True)  # Systematic risk measure
    # alpha = Column(Float, nullable=True)  # Risk-adjusted return measure
    # sharpe_ratio = Column(Float, nullable=True)
    # debt_to_equity = Column(Float, nullable=True)
    # current_ratio = Column(Float, nullable=True)
    # quick_ratio = Column(Float, nullable=True)
    # return_on_equity = Column(Float, nullable=True)
    # return_on_assets = Column(Float, nullable=True)
    # profit_margin = Column(Float, nullable=True)
    #
    # # Performance Metrics
    # ytd_return = Column(Float, nullable=True)
    # one_month_return = Column(Float, nullable=True)
    # three_month_return = Column(Float, nullable=True)
    # six_month_return = Column(Float, nullable=True)
    # one_year_return = Column(Float, nullable=True)
    # three_year_return = Column(Float, nullable=True)
    # five_year_return = Column(Float, nullable=True)
    #
    # # 52-week range
    # week_52_high = Column(Float, nullable=True)
    # week_52_low = Column(Float, nullable=True)
    # week_52_high_date = Column(Date, nullable=True)
    # week_52_low_date = Column(Date, nullable=True)
    #
    # # ESG (Environmental, Social, Governance) Scores
    # esg_score = Column(Float, nullable=True)
    # environmental_score = Column(Float, nullable=True)
    # social_score = Column(Float, nullable=True)
    # governance_score = Column(Float, nullable=True)
    #
    #
    # # Data Quality and Sources
    # data_vendor = Column(String(50), nullable=True)
    # data_quality_score = Column(Float, nullable=True)
    # last_updated = Column(DateTime(timezone=True), nullable=True)
    #
    # # Regulatory and Compliance
    # is_etf = Column(Boolean, nullable=False, default=False)
    # is_reit = Column(Boolean, nullable=False, default=False)
    # is_adr = Column(Boolean, nullable=False, default=False)
    # is_otc = Column(Boolean, nullable=False, default=False)  # Over-the-counter
    #
    # # Trading Constraints
    # short_selling_allowed = Column(Boolean, nullable=True)
    # minimum_lot_size = Column(Integer, nullable=True)
    # tick_size = Column(Float, nullable=True)  # Minimum price increment
