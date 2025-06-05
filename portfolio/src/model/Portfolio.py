from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, Enum, ForeignKey, Index, Integer, NUMERIC, \
    String, Table, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
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

# Association table for many-to-many relationship between Portfolio and Equity
portfolio_equity_association = Table(
    'portfolio_equity',
    Base.metadata,
    Column('portfolio_id', Integer, ForeignKey('portfolio.id'), primary_key=True),
    Column('equity_id', Integer, ForeignKey('equity.id'), primary_key=True),
    Column('currency', Enum(CurrencyEnum), nullable=False),
    Column('weight', NUMERIC(precision=10, scale=6), nullable=False),
    Column('target_weight', NUMERIC(precision=10, scale=6), nullable=True),
    Column('units', NUMERIC(precision=20, scale=6), nullable=True),
    Column('market_value', NUMERIC(precision=20, scale=2), nullable=True),
    Column('added_at', DateTime(timezone=True), server_default=func.now()),
    Column('last_rebalanced_at', DateTime(timezone=True), nullable=True),
    Column('is_active', Boolean, default=True),
    Index('idx_portfolio_equity_portfolio', 'portfolio_id'),
    Index('idx_portfolio_equity_equity', 'equity_id'),
    Index('idx_portfolio_equity_currency', 'currency'),
    CheckConstraint('weight >= 0 AND weight <= 1', name='check_weight_range'),
    CheckConstraint('target_weight IS NULL OR (target_weight >= 0 AND target_weight <= 1)',
                    name='check_target_weight_range')
)

# Association table for many-to-many relationship between Portfolio and Bonds
portfolio_bond_association = Table(
    'portfolio_bond',
    Base.metadata,
    Column('portfolio_id', Integer, ForeignKey('portfolio.id'), primary_key=True),
    Column('bond_id', Integer, ForeignKey('bonds.id'), primary_key=True),
    Column('currency', Enum(CurrencyEnum), nullable=False),
    Column('weight', NUMERIC(precision=10, scale=6), nullable=False),
    Column('target_weight', NUMERIC(precision=10, scale=6), nullable=True),
    Column('units', NUMERIC(precision=20, scale=6), nullable=True),
    Column('market_value', NUMERIC(precision=20, scale=2), nullable=True),
    Column('added_at', DateTime(timezone=True), server_default=func.now()),
    Column('last_rebalanced_at', DateTime(timezone=True), nullable=True),
    Column('is_active', Boolean, default=True),
    Index('idx_portfolio_bond_portfolio', 'portfolio_id'),
    Index('idx_portfolio_bond_bond', 'bond_id'),
    Index('idx_portfolio_equity_currency', 'currency'),
    CheckConstraint('weight >= 0 AND weight <= 1', name='check_bond_weight_range'),
    CheckConstraint('target_weight IS NULL OR (target_weight >= 0 AND target_weight <= 1)',
                    name='check_bond_target_weight_range')
)


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

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    version = Column(Integer, default=1, nullable=False)  # For optimistic locking

    # Portfolio classification
    portfolio_type = Column(Enum(PortfolioTypeEnum), nullable=False)
    base_currency = Column(Enum(CurrencyEnum), nullable=False)
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
    total_shares_outstanding = Column(NUMERIC(precision=20, scale=0), nullable=True, default=1000000)
    minimum_investment = Column(NUMERIC(precision=15, scale=2), nullable=True)

    # Risk and constraints
    risk_level = Column(Enum(RiskLevelEnum), nullable=True)
    max_individual_weight = Column(NUMERIC(precision=5, scale=4), nullable=True, default=0.10)  # 10%
    min_individual_weight = Column(NUMERIC(precision=5, scale=4), nullable=True, default=0.01)  # 1%
    max_sector_weight = Column(NUMERIC(precision=5, scale=4), nullable=True)
    max_country_weight = Column(NUMERIC(precision=5, scale=4), nullable=True)
    cash_target_percentage = Column(NUMERIC(precision=5, scale=4), nullable=True, default=0.05)  # 5%

    # Evaluation and calculation context
    calendar = Column(Enum(CalendarEnum), nullable=False, default=CalendarEnum.TARGET)
    business_day_convention = Column(Enum(BusinessDayConventionEnum), nullable=False,
                                     default=BusinessDayConventionEnum.FOLLOWING)
    last_rebalance_date = Column(Date, nullable=True)
    next_rebalance_date = Column(Date, nullable=True)
    last_nav_calculation_date = Column(Date, nullable=True)

    # Fees and expenses
    management_fee = Column(NUMERIC(precision=5, scale=4),
                            nullable=True)  # Annual fee as decimal (e.g., 0.0075 for 0.75%)
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
    equities = relationship(
        "Equity",
        secondary=portfolio_equity_association,
        back_populates="portfolios",
        lazy="dynamic"
    )

    bonds = relationship(
        "BondBase",
        secondary=portfolio_bond_association,
        back_populates="portfolios",
        lazy="dynamic"
    )

    # Add these fields to your Portfolio class
    # geographic_focus = Column(Enum(GeographicFocusEnum), nullable=True)
    # sector_focus = Column(Enum(SectorFocusEnum), nullable=True, default=SectorFocusEnum.DIVERSIFIED)
    # investment_objective = Column(Enum(InvestmentObjectiveEnum), nullable=False)
    # portfolio_strategy = Column(Enum(PortfolioStrategyEnum), nullable=True)
    # investor_type = Column(Enum(InvestorTypeEnum), nullable=True)
    # liquidity_class = Column(Enum(LiquidityClassEnum), nullable=True)
    # tax_status = Column(Enum(TaxStatusEnum), nullable=True)
    # regulatory_framework = Column(Enum(RegulatoryFrameworkEnum), nullable=True)
    # distribution_policy = Column(Enum(DistributionPolicyEnum), nullable=True)
    # hedging_strategy = Column(Enum(HedgingStrategyEnum), nullable=True, default=HedgingStrategyEnum.UNHEDGED)

    # Performance tracking relationship (if you have a performance table)
    # performance_history = relationship("PortfolioPerformance", back_populates="portfolio")

    def __repr__(self):
        return f"<Portfolio(id={self.id}, symbol='{self.symbol}', name='{self.name}')>"

    # Portfolio management methods
    def add_equity_constituent(self, equity, weight: float, target_weight: Optional[float] = None,
                               units: Optional[float] = None) -> bool:
        """Add an equity constituent to the portfolio"""
        if not self._validate_weight(weight):
            raise ValueError(f"Weight {weight} must be between 0 and 1")

        if target_weight and not self._validate_weight(target_weight):
            raise ValueError(f"Target weight {target_weight} must be between 0 and 1")

        # Check if equity already exists in portfolio
        existing = self._get_equity_association(equity.id)
        if existing:
            return self._update_equity_constituent(equity.id, weight, target_weight, units)

        # Add new equity constituent
        from sqlalchemy import insert
        stmt = insert(portfolio_equity_association).values(
            portfolio_id=self.id,
            equity_id=equity.id,
            currency=equity.currency,
            weight=weight,
            target_weight=target_weight,
            units=units,
            market_value=units * equity.market_price if units and equity.market_price else None
        )

        # Execute through session (this would need to be handled by calling code)
        return True

    def add_bond_constituent(self, bond, weight: float, target_weight: Optional[float] = None,
                             units: Optional[float] = None) -> bool:
        """Add a bond constituent to the portfolio"""
        if not self._validate_weight(weight):
            raise ValueError(f"Weight {weight} must be between 0 and 1")

        if target_weight and not self._validate_weight(target_weight):
            raise ValueError(f"Target weight {target_weight} must be between 0 and 1")

        # Check if bond already exists in portfolio
        existing = self._get_bond_association(bond.id)
        if existing:
            return self._update_bond_constituent(bond.id, weight, target_weight, units)

        # Add new bond constituent
        from sqlalchemy import insert
        stmt = insert(portfolio_bond_association).values(
            portfolio_id=self.id,
            bond_id=bond.id,
            currency=bond.currency,
            weight=weight,
            target_weight=target_weight,
            units=units,
            market_value=units * bond.market_price if units and bond.market_price else None
        )

        return True

    def remove_equity_constituent(self, equity_id: int) -> bool:
        """Remove an equity constituent from the portfolio"""
        from sqlalchemy import delete
        stmt = delete(portfolio_equity_association).where(
            self.id == portfolio_equity_association.c.portfolio_id,
            equity_id == portfolio_equity_association.c.equity_id
        )
        return True

    def remove_bond_constituent(self, bond_id: int) -> bool:
        """Remove a bond constituent from the portfolio"""
        from sqlalchemy import delete
        delete(portfolio_bond_association).where(
            self.id == portfolio_bond_association.c.portfolio_id,
            bond_id == portfolio_bond_association.c.bond_id
        )
        return True

    def update_constituent_weight(self, constituent_id: int, constituent_type: str,
                                  new_weight: float, new_target_weight: Optional[float] = None) -> bool:
        """Update the weight of a constituent"""
        if not self._validate_weight(new_weight):
            raise ValueError(f"Weight {new_weight} must be between 0 and 1")

        if constituent_type.lower() == 'equity':
            return self._update_equity_constituent(constituent_id, new_weight, new_target_weight)
        elif constituent_type.lower() == 'bond':
            return self._update_bond_constituent(constituent_id, new_weight, new_target_weight)
        else:
            raise ValueError(f"Invalid constituent type: {constituent_type}")

    def get_total_weight(self) -> float:
        """Calculate total weight of all constituents"""
        equity_weights = self._get_total_equity_weights()
        bond_weights = self._get_total_bond_weights()
        return equity_weights + bond_weights

    def validate_weights(self) -> Dict[str, Any]:
        """Validate that portfolio weights sum to approximately 1.0"""
        total_weight = self.get_total_weight()
        tolerance = 0.01  # 1% tolerance

        return {
            'is_valid': abs(total_weight - 1.0) <= tolerance,
            'total_weight': total_weight,
            'deviation': total_weight - 1.0,
            'tolerance': tolerance
        }

    def calculate_market_value(self) -> float:
        """Calculate total market value of portfolio"""
        equity_value = self._calculate_equity_market_value()
        bond_value = self._calculate_bond_market_value()
        return equity_value + bond_value

    def needs_rebalancing(self) -> bool:
        """Check if portfolio needs rebalancing based on target weights and thresholds"""
        if not self.auto_rebalance_enabled:
            return False

        # Check if it's time for scheduled rebalancing
        if self.next_rebalance_date and datetime.now().date() >= self.next_rebalance_date:
            return True

        # Check if any constituent has drifted beyond tolerance
        return self._check_drift_tolerance()

    def get_constituent_summary(self) -> Dict[str, Any]:
        """Get summary of all constituents"""
        return {
            'equity_count': self.equities.count(),
            'bond_count': self.bonds.count(),
            'total_constituents': self.equities.count() + self.bonds.count(),
            'total_market_value': self.calculate_market_value(),
            'total_weight': self.get_total_weight(),
            'last_updated': self.updated_at
        }

    # Private helper methods
    @staticmethod
    def _validate_weight(weight: float) -> bool:
        """Validate weight is between 0 and 1"""
        return 0 <= weight <= 1

    def _get_equity_association(self, equity_id: int):
        """Get equity association record"""
        # This would need session access to query the association table
        pass

    def _get_bond_association(self, bond_id: int):
        """Get bond association record"""
        # This would need session access to query the association table
        pass

    def _update_equity_constituent(self, equity_id: int, weight: float,
                                   target_weight: Optional[float] = None, units: Optional[float] = None) -> bool:
        """Update existing equity constituent"""
        from sqlalchemy import update
        update(portfolio_equity_association).where(
            self.id == portfolio_equity_association.c.portfolio_id,
            equity_id == portfolio_equity_association.c.equity_id
        ).values(
            weight=weight,
            target_weight=target_weight,
            units=units,
            last_rebalanced_at=func.now()
        )
        return True

    def _update_bond_constituent(self, bond_id: int, weight: float,
                                 target_weight: Optional[float] = None, units: Optional[float] = None) -> bool:
        """Update existing bond constituent"""
        from sqlalchemy import update
        update(portfolio_bond_association).where(
            self.id == portfolio_bond_association.c.portfolio_id,
            bond_id == portfolio_bond_association.c.bond_id
        ).values(
            weight=weight,
            target_weight=target_weight,
            units=units,
            last_rebalanced_at=func.now()
        )
        return True

    def _get_total_equity_weights(self) -> float:
        """Calculate total weight of equity constituents"""
        # This would need session access to sum weights
        return 0.0

    def _get_total_bond_weights(self) -> float:
        """Calculate total weight of bond constituents"""
        # This would need session access to sum weights
        return 0.0

    def _calculate_equity_market_value(self) -> float:
        """Calculate total market value of equity holdings"""
        # This would need session access to calculate
        return 0.0

    def _calculate_bond_market_value(self) -> float:
        """Calculate total market value of bond holdings"""
        # This would need session access to calculate
        return 0.0

    def _check_drift_tolerance(self) -> bool:
        """Check if any constituent has drifted beyond acceptable tolerance"""
        # This would implement logic to check if current weights vs target weights
        # exceed the drift tolerance threshold
        return False
