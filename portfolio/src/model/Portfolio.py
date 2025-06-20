from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Index, Integer, NUMERIC, \
    String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

from portfolio.src.database import Base
from portfolio.src.model.enums.AssetClassEnum import AssetClassEnum
from portfolio.src.model.enums.BusinessDayConventionEnum import BusinessDayConventionEnum
from portfolio.src.model.enums.CalenderEnum import CalendarEnum
from portfolio.src.model.enums.CurrencyEnum import CurrencyEnum
from portfolio.src.model.enums.PortfolioStatusEnum import PortfolioStatusEnum
from portfolio.src.model.enums.PortfolioTypeEnum import PortfolioTypeEnum
from portfolio.src.model.enums.RebalanceFrequencyEnum import RebalanceFrequencyEnum
from portfolio.src.model.enums.RiskLevelEnum import RiskLevelEnum
from portfolio.src.model.enums.WeightingMethodologyEnum import WeightingMethodologyEnum


class Portfolio(Base):
    __tablename__ = 'portfolio'
    __table_args__ = (
        Index('idx_portfolio_symbol', 'symbol'),
        Index('idx_portfolio_currency', 'currency'),
        Index('idx_portfolio_status', 'status'),
        Index('idx_portfolio_created_at', 'created_at'),
        Index('idx_portfolio_inception_date', 'inception_date'),
        UniqueConstraint('symbol', name='uq_portfolio_symbol'),
    )

    API_Path = "Portfolio"

    # Primary identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(100), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Add version tracking fields
    version = Column(Integer, ForeignKey('portfolio_version.id'), nullable=True)
    version_hash = association_proxy('current_version', 'version_hash')

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Portfolio classification
    portfolio_type = Column(Enum(PortfolioTypeEnum), nullable=False)
    currency = Column(Enum(CurrencyEnum), nullable=False)
    asset_class = Column(Enum(AssetClassEnum), nullable=False)

    # Portfolio methodology and strategy
    weighting_methodology = Column(Enum(WeightingMethodologyEnum), nullable=False)
    rebalance_frequency = Column(Enum(RebalanceFrequencyEnum), nullable=False)
    benchmark_symbol = Column(String(100), nullable=True)
    strategy_description = Column(Text, nullable=True)

    # Portfolio lifecycle
    inception_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)
    status = Column(Enum(PortfolioStatusEnum), nullable=False, default=PortfolioStatusEnum.ACTIVE)

    # Financial metrics
    total_market_value = Column(NUMERIC(precision=20, scale=2), nullable=True)
    nav_per_share = Column(NUMERIC(precision=15, scale=6), nullable=True)
    total_shares_outstanding = Column(NUMERIC(precision=20, scale=0), nullable=True)
    minimum_investment = Column(NUMERIC(precision=15, scale=2), nullable=True)

    # Risk and constraints
    risk_level = Column(Enum(RiskLevelEnum), nullable=True)
    max_individual_weight = Column(NUMERIC(precision=5, scale=4), nullable=True)
    min_individual_weight = Column(NUMERIC(precision=5, scale=4), nullable=True)
    max_sector_weight = Column(NUMERIC(precision=5, scale=4), nullable=True)
    max_country_weight = Column(NUMERIC(precision=5, scale=4), nullable=True)
    cash_target_percentage = Column(NUMERIC(precision=5, scale=4), nullable=True)

    # Evaluation and calculation context
    calendar = Column(Enum(CalendarEnum), nullable=False, default=CalendarEnum.TARGET)
    business_day_convention = Column(Enum(BusinessDayConventionEnum), nullable=False,
                                     default=BusinessDayConventionEnum.FOLLOWING)
    last_rebalance_date = Column(Date, nullable=True)
    next_rebalance_date = Column(Date, nullable=True)
    last_nav_calculation_date = Column(Date, nullable=True)

    # Fees and expenses
    management_fee = Column(NUMERIC(precision=5, scale=4), nullable=True)
    performance_fee = Column(NUMERIC(precision=5, scale=4), nullable=True)
    expense_ratio = Column(NUMERIC(precision=5, scale=4), nullable=True)

    # Operational fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    allow_fractional_shares = Column(Boolean, default=True, nullable=False)
    auto_rebalance_enabled = Column(Boolean, default=False, nullable=False)

    # Metadata and configuration
    custom_fields = Column(JSONB, nullable=True, default=dict)  # For extensibility
    compliance_rules = Column(JSONB, nullable=True, default=list)
    tags = Column(JSONB, nullable=True, default=list)

    # Manager/Administrator information
    portfolio_manager = Column(String(200), nullable=True)
    administrator = Column(String(200), nullable=True)
    custodian = Column(String(200), nullable=True)

    # Relationships
    versions = relationship(
        "PortfolioVersion",
        back_populates="portfolio",
        order_by="desc(PortfolioVersion.version_id)",
        lazy="dynamic"
    )

    constituents = relationship(
        "Constituent",
        back_populates="portfolio",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Portfolio(id={self.id}, symbol='{self.symbol}', name='{self.name}', version={self.version})>"

    # # Portfolio management methods
    # def add_constituent(self, asset_id: int, asset_class: AssetClassEnum, currency: CurrencyEnum,
    #                     weight: float, target_weight: Optional[float] = None,
    #                     units: float = None, constituent: float = None) -> Constituent:
    #     """Add a constituent to the portfolio"""
    #     if not self._validate_weight(weight):
    #         raise ValueError(f"Weight {weight} must be between 0 and 1")
    #
    #     if target_weight and not self._validate_weight(target_weight):
    #         raise ValueError(f"Target weight {target_weight} must be between 0 and 1")
    #
    #     market_value = units * constituent.market_price
    #
    #     constituent = Constituent(
    #         portfolio_id=self.id,
    #         asset_id=asset_id,
    #         asset_class=asset_class,
    #         currency=currency,
    #         weight=weight,
    #         target_weight=target_weight,
    #         units=units,
    #         market_value=market_value
    #     )
    #
    #     return constituent
    #
    # def remove_constituent_by_constituent_id(self, session: get_db(), constituent_id: int) -> bool:
    #     """Remove a constituent from the portfolio"""
    #     constituent = session.query(Constituent).filter_by(
    #         portfolio_id=self.id,
    #         id=constituent_id
    #     ).first()
    #
    #     if not constituent:
    #         return False
    #
    #     session.delete(constituent)
    #     return True
    #
    # def remove_constituent_by_asset_id_and_class(self, session: get_db(), asset_id: int,
    #                                              asset_class: AssetClassEnum) -> bool:
    #     """Remove a constituent from the portfolio"""
    #     constituent = session.query(Constituent).filter_by(
    #         portfolio_id=self.id,
    #         id=asset_id,
    #         asset_class=asset_class
    #     ).first()
    #
    #     if not constituent:
    #         return False
    #
    #     session.delete(constituent)
    #     return True
    #
    # def update_constituent(self, session: get_db(), constituent_id: int,
    #                        weight: Optional[float] = None,
    #                        target_weight: Optional[float] = None,
    #                        units: Optional[float] = None,
    #                        market_price: Optional[float] = None,
    #                        is_active: Optional[bool] = None) -> bool:
    #     """Update a constituent's properties"""
    #     update_data = {}
    #
    #     if weight is not None:
    #         if not self._validate_weight(weight):
    #             raise ValueError(f"Weight {weight} must be between 0 and 1")
    #         update_data['weight'] = weight
    #
    #     if target_weight is not None:
    #         if not self._validate_weight(target_weight):
    #             raise ValueError(f"Target weight {target_weight} must be between 0 and 1")
    #         update_data['target_weight'] = target_weight
    #
    #     if units is not None:
    #         update_data['units'] = units
    #
    #     if market_price is not None and units is not None:
    #         update_data['market_value'] = units * market_price
    #
    #     if is_active is not None:
    #         update_data['is_active'] = is_active
    #
    #     if not update_data:
    #         return False  # Nothing to update
    #
    #     update_data['last_rebalanced_at'] = func.now()
    #
    #     stmt = update(Constituent).where(
    #         constituent_id == Constituent.id,
    #         self.id == Constituent.portfolio_id
    #     ).values(**update_data)
    #
    #     result = session.execute(stmt)
    #     return result.rowcount > 0
    #
    # def get_constituent(self, session: get_db(), constituent_id: int) -> Optional[Constituent]:
    #     """Get a specific constituent by ID"""
    #     return session.query(Constituent).filter_by(
    #         portfolio_id=self.id,
    #         id=constituent_id
    #     ).first()
    #
    # def get_constituents(self, session: get_db(),
    #                      asset_class: Optional[AssetClassEnum] = None,
    #                      active_only: bool = True) -> List[Constituent]:
    #     """Get all constituents, optionally filtered by asset class and active status"""
    #     query = session.query(Constituent).filter_by(portfolio_id=self.id)
    #
    #     if asset_class:
    #         query = query.filter_by(asset_class=asset_class)
    #
    #     if active_only:
    #         query = query.filter_by(is_active=True)
    #
    #     return query.all()
    #
    # def get_total_weight(self, session: get_db(), active_only: bool = True) -> float:
    #     """Calculate total weight of all constituents"""
    #     query = session.query(func.sum(Constituent.weight)).filter_by(portfolio_id=self.id)
    #
    #     if active_only:
    #         query = query.filter_by(is_active=True)
    #
    #     total = query.scalar()
    #     return total if total else 0.0
    #
    # def validate_weights(self, session: get_db()) -> Dict[str, Any]:
    #     """Validate that portfolio weights sum to approximately 1.0"""
    #     total_weight = self.get_total_weight(session)
    #     tolerance = 0.01  # 1% tolerance
    #
    #     return {
    #         'is_valid': abs(total_weight - 1.0) <= tolerance,
    #         'total_weight': total_weight,
    #         'deviation': total_weight - 1.0,
    #         'tolerance': tolerance
    #     }
    #
    # def calculate_market_value(self, session: get_db(), active_only: bool = True) -> float:
    #     """Calculate total market value of portfolio"""
    #     query = session.query(func.sum(Constituent.market_value)).filter_by(portfolio_id=self.id)
    #
    #     if active_only:
    #         query = query.filter_by(is_active=True)
    #
    #     total = query.scalar()
    #     return total if total else 0.0
    #
    # def needs_rebalancing(self, session: get_db()) -> bool:
    #     """Check if portfolio needs rebalancing based on target weights and thresholds"""
    #     if not self.auto_rebalance_enabled:
    #         return False
    #
    #     # Check if it's time for scheduled rebalancing
    #     if self.next_rebalance_date and datetime.now().date() >= self.next_rebalance_date:
    #         return True
    #
    #     # Check if any constituent has drifted beyond tolerance
    #     return self._check_drift_tolerance(session)
    #
    # def get_constituent_summary(self, session: get_db()) -> Dict[str, Any]:
    #     """Get summary of all constituents"""
    #     equity_count = session.query(Constituent).filter_by(
    #         portfolio_id=self.id,
    #         asset_class=AssetClassEnum.EQUITY,
    #         is_active=True
    #     ).count()
    #
    #     fixed_income_count = session.query(Constituent).filter_by(
    #         portfolio_id=self.id,
    #         asset_class=AssetClassEnum.FIXED_INCOME,
    #         is_active=True
    #     ).count()
    #
    #     return {
    #         'equity_count': equity_count,
    #         'fixed_income_count': fixed_income_count,
    #         'total_constituents': equity_count + fixed_income_count,
    #         'total_market_value': self.calculate_market_value(session),
    #         'total_weight': self.get_total_weight(session),
    #         'last_updated': self.updated_at
    #     }
    #
    # def rebalance_portfolio(self, session: get_db()) -> bool:
    #     """Rebalance the portfolio to target weights"""
    #     if not self.auto_rebalance_enabled:
    #         return False
    #
    #     # Get all active constituents with target weights
    #     constituents = session.query(Constituent).filter(
    #         Constituent.portfolio_id == self.id,
    #         Constituent.is_active == True,
    #         Constituent.target_weight.isnot(None)
    #     ).all()
    #
    #     if not constituents:
    #         return False
    #
    #     # Update weights to match target weights
    #     for constituent in constituents:
    #         constituent.weight = constituent.target_weight
    #         constituent.last_rebalanced_at = func.now()
    #
    #     # Update portfolio rebalance dates
    #     self.last_rebalance_date = func.now()
    #
    #     # Calculate next rebalance date based on frequency
    #     self._calculate_next_rebalance_date()
    #
    #     return True
    #
    #     # Private helper methods
    #
    # @staticmethod
    # def _validate_weight(weight: float) -> bool:
    #     """Validate weight is between 0 and 1"""
    #     return 0 <= weight <= 1
    #
    # def get_equity_constituents(self):
    #     """Get all equity constituents"""
    #     return self.constituents.filter_by(asset_class=AssetClassEnum.EQUITY)
    #
    # def get_fixed_income_constituents(self):
    #     """Get all fixed income constituents"""
    #     return self.constituents.filter_by(asset_class=AssetClassEnum.FIXED_INCOME)
    #
    # def _check_drift_tolerance(self, session: get_db()) -> bool:
    #     """Check if any constituent has drifted beyond acceptable tolerance"""
    #     tolerance = 0.05  # 5% drift tolerance
    #
    #     drifted_constituents = session.query(Constituent).filter(
    #         Constituent.portfolio_id == self.id,
    #         Constituent.is_active == True,
    #         Constituent.target_weight.isnot(None),
    #         or_(
    #             Constituent.weight - Constituent.target_weight > tolerance,
    #             Constituent.target_weight - Constituent.weight > tolerance
    #         )
    #     ).exists()
    #
    #     return session.query(drifted_constituents).scalar()
    #
    # def _calculate_next_rebalance_date(self):
    #     """Calculate next rebalance date based on frequency"""
    #     if not self.rebalance_frequency or not self.last_rebalance_date:
    #         return
    #     try:
    #
    #         last_rebalance = to_ql_date(self.last_rebalance_date)
    #         calendar = to_ql_calendar(self.calendar)
    #         convention = to_ql_business_day_convention(self.business_day_convention)
    #
    #         # Determine the period based on rebalance frequency
    #         if self.rebalance_frequency == RebalanceFrequencyEnum.DAILY:
    #             period = Period(1, Days)
    #         elif self.rebalance_frequency == RebalanceFrequencyEnum.WEEKLY:
    #             period = Period(1, Weeks)
    #         elif self.rebalance_frequency == RebalanceFrequencyEnum.MONTHLY:
    #             period = Period(1, Months)
    #         elif self.rebalance_frequency == RebalanceFrequencyEnum.QUARTERLY:
    #             period = Period(3, Months)
    #         elif self.rebalance_frequency == RebalanceFrequencyEnum.ANNUALLY:
    #             period = Period(1, Years)
    #         else:
    #             return
    #
    #         # Calculate the adjusted date
    #         next_date = calendar.advance(last_rebalance, period, convention)
    #
    #         # Convert back to Python date
    #         self.next_rebalance_date = from_ql_date(next_date)
    #
    #     except ValueError as e:
    #         # Fallback to simple date arithmetic if mapping fails
    #         import warnings
    #         warnings.warn(f"QuantLib calendar/conversion failed: {str(e)}. Using simple date arithmetic.")
    #
    #         if self.rebalance_frequency == RebalanceFrequencyEnum.DAILY:
    #             self.next_rebalance_date = self.last_rebalance_date + timedelta(days=1)
    #         elif self.rebalance_frequency == RebalanceFrequencyEnum.WEEKLY:
    #             self.next_rebalance_date = self.last_rebalance_date + timedelta(weeks=1)
    #         elif self.rebalance_frequency == RebalanceFrequencyEnum.MONTHLY:
    #             self.next_rebalance_date = self.last_rebalance_date + relativedelta(months=1)
    #         elif self.rebalance_frequency == RebalanceFrequencyEnum.QUARTERLY:
    #             self.next_rebalance_date = self.last_rebalance_date + relativedelta(months=3)
    #         elif self.rebalance_frequency == RebalanceFrequencyEnum.ANNUALLY:
    #             self.next_rebalance_date = self.last_rebalance_date + relativedelta(years=1)
