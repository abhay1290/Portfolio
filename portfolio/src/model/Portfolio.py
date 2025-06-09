from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from QuantLib import Days, Months, Period, Weeks, Years
from dateutil.relativedelta import relativedelta
from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Index, Integer, NUMERIC, \
    String, Text, UniqueConstraint, func, or_, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from portfolio.src.database import Base, get_db
from portfolio.src.model.Constituent import Constituent
from portfolio.src.model.enums.AssetClassEnum import AssetClassEnum
from portfolio.src.model.enums.BusinessDayConventionEnum import BusinessDayConventionEnum
from portfolio.src.model.enums.CalenderEnum import CalendarEnum
from portfolio.src.model.enums.CurrencyEnum import CurrencyEnum
from portfolio.src.model.enums.PortfolioStatusEnum import PortfolioStatusEnum
from portfolio.src.model.enums.PortfolioTypeEnum import PortfolioTypeEnum
from portfolio.src.model.enums.RebalanceFrequencyEnum import RebalanceFrequencyEnum
from portfolio.src.model.enums.RiskLevelEnum import RiskLevelEnum
from portfolio.src.model.enums.WeightingMethodologyEnum import WeightingMethodologyEnum
from portfolio.src.utils.quantlib_mapper import from_ql_date, to_ql_business_day_convention, to_ql_calendar, to_ql_date


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
    constituents = relationship(
        "Constituent",
        back_populates="portfolio",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Portfolio(id={self.id}, symbol='{self.symbol}', name='{self.name}', version={self.version})>"

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

    # Portfolio management methods
    def add_constituent(self, asset_id: int, asset_class: AssetClassEnum, currency: CurrencyEnum,
                        weight: float, target_weight: Optional[float] = None,
                        units: float = None, constituent: float = None) -> Constituent:
        """Add a constituent to the portfolio"""
        if not self._validate_weight(weight):
            raise ValueError(f"Weight {weight} must be between 0 and 1")

        if target_weight and not self._validate_weight(target_weight):
            raise ValueError(f"Target weight {target_weight} must be between 0 and 1")

        market_value = units * constituent.market_price

        constituent = Constituent(
            portfolio_id=self.id,
            asset_id=asset_id,
            asset_class=asset_class,
            currency=currency,
            weight=weight,
            target_weight=target_weight,
            units=units,
            market_value=market_value
        )

        return constituent

    def remove_constituent_by_constituent_id(self, session: get_db(), constituent_id: int) -> bool:
        """Remove a constituent from the portfolio"""
        constituent = session.query(Constituent).filter_by(
            portfolio_id=self.id,
            id=constituent_id
        ).first()

        if not constituent:
            return False

        session.delete(constituent)
        return True

    def remove_constituent_by_asset_id_and_class(self, session: get_db(), asset_id: int,
                                                 asset_class: AssetClassEnum) -> bool:
        """Remove a constituent from the portfolio"""
        constituent = session.query(Constituent).filter_by(
            portfolio_id=self.id,
            id=asset_id,
            asset_class=asset_class
        ).first()

        if not constituent:
            return False

        session.delete(constituent)
        return True

    def update_constituent(self, session: get_db(), constituent_id: int,
                           weight: Optional[float] = None,
                           target_weight: Optional[float] = None,
                           units: Optional[float] = None,
                           market_price: Optional[float] = None,
                           is_active: Optional[bool] = None) -> bool:
        """Update a constituent's properties"""
        update_data = {}

        if weight is not None:
            if not self._validate_weight(weight):
                raise ValueError(f"Weight {weight} must be between 0 and 1")
            update_data['weight'] = weight

        if target_weight is not None:
            if not self._validate_weight(target_weight):
                raise ValueError(f"Target weight {target_weight} must be between 0 and 1")
            update_data['target_weight'] = target_weight

        if units is not None:
            update_data['units'] = units

        if market_price is not None and units is not None:
            update_data['market_value'] = units * market_price

        if is_active is not None:
            update_data['is_active'] = is_active

        if not update_data:
            return False  # Nothing to update

        update_data['last_rebalanced_at'] = func.now()

        stmt = update(Constituent).where(
            constituent_id == Constituent.id,
            self.id == Constituent.portfolio_id
        ).values(**update_data)

        result = session.execute(stmt)
        return result.rowcount > 0

    def get_constituent(self, session: get_db(), constituent_id: int) -> Optional[Constituent]:
        """Get a specific constituent by ID"""
        return session.query(Constituent).filter_by(
            portfolio_id=self.id,
            id=constituent_id
        ).first()

    def get_constituents(self, session: get_db(),
                         asset_class: Optional[AssetClassEnum] = None,
                         active_only: bool = True) -> List[Constituent]:
        """Get all constituents, optionally filtered by asset class and active status"""
        query = session.query(Constituent).filter_by(portfolio_id=self.id)

        if asset_class:
            query = query.filter_by(asset_class=asset_class)

        if active_only:
            query = query.filter_by(is_active=True)

        return query.all()

    def get_total_weight(self, session: get_db(), active_only: bool = True) -> float:
        """Calculate total weight of all constituents"""
        query = session.query(func.sum(Constituent.weight)).filter_by(portfolio_id=self.id)

        if active_only:
            query = query.filter_by(is_active=True)

        total = query.scalar()
        return total if total else 0.0

    def validate_weights(self, session: get_db()) -> Dict[str, Any]:
        """Validate that portfolio weights sum to approximately 1.0"""
        total_weight = self.get_total_weight(session)
        tolerance = 0.01  # 1% tolerance

        return {
            'is_valid': abs(total_weight - 1.0) <= tolerance,
            'total_weight': total_weight,
            'deviation': total_weight - 1.0,
            'tolerance': tolerance
        }

    def calculate_market_value(self, session: get_db(), active_only: bool = True) -> float:
        """Calculate total market value of portfolio"""
        query = session.query(func.sum(Constituent.market_value)).filter_by(portfolio_id=self.id)

        if active_only:
            query = query.filter_by(is_active=True)

        total = query.scalar()
        return total if total else 0.0

    def needs_rebalancing(self, session: get_db()) -> bool:
        """Check if portfolio needs rebalancing based on target weights and thresholds"""
        if not self.auto_rebalance_enabled:
            return False

        # Check if it's time for scheduled rebalancing
        if self.next_rebalance_date and datetime.now().date() >= self.next_rebalance_date:
            return True

        # Check if any constituent has drifted beyond tolerance
        return self._check_drift_tolerance(session)

    def get_constituent_summary(self, session: get_db()) -> Dict[str, Any]:
        """Get summary of all constituents"""
        equity_count = session.query(Constituent).filter_by(
            portfolio_id=self.id,
            asset_class=AssetClassEnum.EQUITY,
            is_active=True
        ).count()

        fixed_income_count = session.query(Constituent).filter_by(
            portfolio_id=self.id,
            asset_class=AssetClassEnum.FIXED_INCOME,
            is_active=True
        ).count()

        return {
            'equity_count': equity_count,
            'fixed_income_count': fixed_income_count,
            'total_constituents': equity_count + fixed_income_count,
            'total_market_value': self.calculate_market_value(session),
            'total_weight': self.get_total_weight(session),
            'last_updated': self.updated_at
        }

    def rebalance_portfolio(self, session: get_db()) -> bool:
        """Rebalance the portfolio to target weights"""
        if not self.auto_rebalance_enabled:
            return False

        # Get all active constituents with target weights
        constituents = session.query(Constituent).filter(
            Constituent.portfolio_id == self.id,
            Constituent.is_active == True,
            Constituent.target_weight.isnot(None)
        ).all()

        if not constituents:
            return False

        # Update weights to match target weights
        for constituent in constituents:
            constituent.weight = constituent.target_weight
            constituent.last_rebalanced_at = func.now()

        # Update portfolio rebalance dates
        self.last_rebalance_date = func.now()

        # Calculate next rebalance date based on frequency
        self._calculate_next_rebalance_date()

        return True

        # Private helper methods

    @staticmethod
    def _validate_weight(weight: float) -> bool:
        """Validate weight is between 0 and 1"""
        return 0 <= weight <= 1

    def get_equity_constituents(self):
        """Get all equity constituents"""
        return self.constituents.filter_by(asset_class=AssetClassEnum.EQUITY)

    def get_fixed_income_constituents(self):
        """Get all fixed income constituents"""
        return self.constituents.filter_by(asset_class=AssetClassEnum.FIXED_INCOME)

    def _check_drift_tolerance(self, session: get_db()) -> bool:
        """Check if any constituent has drifted beyond acceptable tolerance"""
        tolerance = 0.05  # 5% drift tolerance

        drifted_constituents = session.query(Constituent).filter(
            Constituent.portfolio_id == self.id,
            Constituent.is_active == True,
            Constituent.target_weight.isnot(None),
            or_(
                Constituent.weight - Constituent.target_weight > tolerance,
                Constituent.target_weight - Constituent.weight > tolerance
            )
        ).exists()

        return session.query(drifted_constituents).scalar()

    def _calculate_next_rebalance_date(self):
        """Calculate next rebalance date based on frequency"""
        if not self.rebalance_frequency or not self.last_rebalance_date:
            return
        try:

            last_rebalance = to_ql_date(self.last_rebalance_date)
            calendar = to_ql_calendar(self.calendar)
            convention = to_ql_business_day_convention(self.business_day_convention)

            # Determine the period based on rebalance frequency
            if self.rebalance_frequency == RebalanceFrequencyEnum.DAILY:
                period = Period(1, Days)
            elif self.rebalance_frequency == RebalanceFrequencyEnum.WEEKLY:
                period = Period(1, Weeks)
            elif self.rebalance_frequency == RebalanceFrequencyEnum.MONTHLY:
                period = Period(1, Months)
            elif self.rebalance_frequency == RebalanceFrequencyEnum.QUARTERLY:
                period = Period(3, Months)
            elif self.rebalance_frequency == RebalanceFrequencyEnum.ANNUALLY:
                period = Period(1, Years)
            else:
                return

            # Calculate the adjusted date
            next_date = calendar.advance(last_rebalance, period, convention)

            # Convert back to Python date
            self.next_rebalance_date = from_ql_date(next_date)

        except ValueError as e:
            # Fallback to simple date arithmetic if mapping fails
            import warnings
            warnings.warn(f"QuantLib calendar/conversion failed: {str(e)}. Using simple date arithmetic.")

            if self.rebalance_frequency == RebalanceFrequencyEnum.DAILY:
                self.next_rebalance_date = self.last_rebalance_date + timedelta(days=1)
            elif self.rebalance_frequency == RebalanceFrequencyEnum.WEEKLY:
                self.next_rebalance_date = self.last_rebalance_date + timedelta(weeks=1)
            elif self.rebalance_frequency == RebalanceFrequencyEnum.MONTHLY:
                self.next_rebalance_date = self.last_rebalance_date + relativedelta(months=1)
            elif self.rebalance_frequency == RebalanceFrequencyEnum.QUARTERLY:
                self.next_rebalance_date = self.last_rebalance_date + relativedelta(months=3)
            elif self.rebalance_frequency == RebalanceFrequencyEnum.ANNUALLY:
                self.next_rebalance_date = self.last_rebalance_date + relativedelta(years=1)

    # ========== VERSIONING METHODS ==========

    def get_versions(self, session: get_db()) -> List['PortfolioVersion']:
        """Get all versions of this portfolio"""
        VersionClass = self.get_version_class()
        return session.query(VersionClass).filter(
            VersionClass.id == self.id
        ).order_by(VersionClass.transaction_id).all()

    def get_version_at_date(self, session: get_db(), target_date: datetime) -> Optional['PortfolioVersion']:
        """Get the version that was active at a specific date"""
        VersionClass = self.get_version_class()
        return session.query(VersionClass).filter(
            VersionClass.id == self.id,
            VersionClass.transaction.has(
                func.date(VersionClass.transaction.issued_at) <= target_date.date()
            )
        ).order_by(desc(VersionClass.transaction_id)).first()

    def get_version_by_number(self, session: get_db(), version_number: int) -> Optional['PortfolioVersion']:
        """Get a specific version by version number"""
        VersionClass = self.get_version_class()
        return session.query(VersionClass).filter(
            VersionClass.id == self.id,
            VersionClass.version == version_number
        ).first()

    def rollback_to_version(self, session: get_db(), target_version: int,
                            change_reason: str = None, approved_by: str = None) -> bool:
        """
        Rollback to a specific version and create a new version with the old state.
        This preserves the audit trail.
        """
        try:
            # Get the target version
            target_version_obj = self.get_version_by_number(session, target_version)
            if not target_version_obj:
                raise ValueError(f"Version {target_version} not found")

            # Store current version for potential recovery
            current_state = self._create_state_snapshot()

            # Apply the target version's state to current object
            self._apply_version_state(target_version_obj)

            # Update versioning metadata
            self.version += 1
            self.change_reason = change_reason or f"Rollback to version {target_version}"
            self.approved_by = approved_by
            self.updated_at = func.now()

            # Generate new version hash
            self.version_hash = self._generate_version_hash()

            session.flush()  # This will create a new version automatically
            return True

        except Exception as e:
            session.rollback()
            raise Exception(f"Rollback failed: {str(e)}")

    def rollback_and_replay(self, session: get_db(), exclude_version: int,
                            change_reason: str = None, approved_by: str = None) -> bool:
        """
        Advanced rollback: Rollback to before a specific version, then replay all
        subsequent versions except the excluded one.
        """
        try:
            versions = self.get_versions(session)
            if not versions:
                return False

            # Find the excluded version and get all versions after it
            exclude_index = None
            for i, version in enumerate(versions):
                if version.version == exclude_version:
                    exclude_index = i
                    break

            if exclude_index is None:
                raise ValueError(f"Version {exclude_version} not found")

            # Get the version just before the excluded one
            if exclude_index == 0:
                # If excluding the first version, start from initial state
                baseline_version = None
            else:
                baseline_version = versions[exclude_index - 1]

            # Rollback to baseline
            if baseline_version:
                self._apply_version_state(baseline_version)
            else:
                self._reset_to_initial_state()

            # Replay all versions after the excluded one
            versions_to_replay = versions[exclude_index + 1:]
            for replay_version in versions_to_replay:
                self._apply_version_changes(replay_version)

            # Update metadata
            self.version += 1
            self.change_reason = change_reason or f"Rollback excluding version {exclude_version}"
            self.approved_by = approved_by
            self.updated_at = func.now()
            self.version_hash = self._generate_version_hash()

            session.flush()
            return True

        except Exception as e:
            session.rollback()
            raise Exception(f"Rollback and replay failed: {str(e)}")

    def get_version_diff(self, session: get_db(), version1: int, version2: int) -> Dict[str, Any]:
        """Compare two versions and return the differences"""
        v1 = self.get_version_by_number(session, version1)
        v2 = self.get_version_by_number(session, version2)

        if not v1 or not v2:
            raise ValueError("One or both versions not found")

        diff = {
            'version1': version1,
            'version2': version2,
            'changes': {},
            'timestamp1': v1.transaction.issued_at if hasattr(v1, 'transaction') else None,
            'timestamp2': v2.transaction.issued_at if hasattr(v2, 'transaction') else None,
        }

        # Compare all versioned columns
        for column in self.__table__.columns:
            if column.name not in self.__versioned__.get('exclude', []):
                val1 = getattr(v1, column.name, None)
                val2 = getattr(v2, column.name, None)

                if val1 != val2:
                    diff['changes'][column.name] = {
                        'from': val1,
                        'to': val2
                    }

        return diff

    def get_version_timeline(self, session: get_db()) -> List[Dict[str, Any]]:
        """Get a timeline of all changes with metadata"""
        versions = self.get_versions(session)
        timeline = []

        for version in versions:
            timeline.append({
                'version': version.version,
                'timestamp': version.transaction.issued_at if hasattr(version, 'transaction') else None,
                'change_reason': getattr(version, 'change_reason', None),
                'approved_by': getattr(version, 'approved_by', None),
                'version_hash': getattr(version, 'version_hash', None),
                'operation_type': getattr(version, 'operation_type', None),
            })

        return timeline

    def _apply_version_state(self, version_obj):
        """Apply a version's state to the current object"""
        for column in self.__table__.columns:
            if column.name not in ['id', 'created_at', 'updated_at']:
                if hasattr(version_obj, column.name):
                    setattr(self, column.name, getattr(version_obj, column.name))

    def _apply_version_changes(self, version_obj):
        """Apply incremental changes from a version"""
        # This would contain logic to apply only the changed fields
        # For now, we'll apply the full state
        self._apply_version_state(version_obj)

    def _create_state_snapshot(self) -> Dict[str, Any]:
        """Create a snapshot of current state for backup purposes"""
        snapshot = {}
        for column in self.__table__.columns:
            snapshot[column.name] = getattr(self, column.name)
        return snapshot

    def _reset_to_initial_state(self):
        """Reset object to initial state (for replay scenarios)"""
        # This would reset to the state at creation
        # Implementation depends on your business logic
        pass

    def _generate_version_hash(self):
        """Generate a hash representing the current state"""
        import hashlib
        import json

        state_dict = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Convert non-serializable types
            if hasattr(value, 'isoformat'):  # datetime objects
                value = value.isoformat()
            elif hasattr(value, '__dict__'):  # enum objects
                value = str(value)
            state_dict[column.name] = value

        state_json = json.dumps(state_dict, sort_keys=True, default=str)
        return hashlib.sha256(state_json.encode()).hexdigest()

    configure_mappers()
