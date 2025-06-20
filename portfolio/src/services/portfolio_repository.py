from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from portfolio.src.api.schemas.portfolio_schema import PortfolioRequest
from portfolio.src.model import Constituent, Portfolio
from portfolio.src.model.enums import AssetClassEnum


class PortfolioRepository:
    """Data access layer for portfolio operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, portfolio_id: int) -> Optional[Portfolio]:
        """Get portfolio by ID"""
        return self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

    def get_with_constituents(self, portfolio_id: int) -> Optional[Portfolio]:
        """Get portfolio with eager-loaded constituents"""
        return (
            self.db.query(Portfolio)
            .options(joinedload(Portfolio.constituents))
            .filter(Portfolio.id == portfolio_id)
            .first()
        )

    def exists(self, portfolio_id: Optional[int], symbol: str) -> bool:
        """Check if portfolio exists by ID or symbol"""
        query = self.db.query(Portfolio)
        if portfolio_id:
            query = query.filter(Portfolio.id == portfolio_id)
        return query.first() is not None

    def create_portfolio(self, portfolio_data: PortfolioRequest) -> Portfolio:
        """Create portfolio entity"""
        portfolio = Portfolio(
            # Primary identifiers
            symbol=portfolio_data.symbol,
            name=portfolio_data.name,
            description=portfolio_data.description,

            # Portfolio classification
            portfolio_type=portfolio_data.portfolio_type,
            base_currency=portfolio_data.base_currency,
            asset_class=portfolio_data.asset_class,

            # Portfolio methodology and strategy
            weighting_methodology=portfolio_data.weighting_methodology,
            rebalance_frequency=portfolio_data.rebalance_frequency,
            benchmark_symbol=portfolio_data.benchmark_symbol,
            strategy_description=portfolio_data.strategy_description,

            # Portfolio lifecycle
            inception_date=portfolio_data.inception_date,
            termination_date=portfolio_data.termination_date,
            status=portfolio_data.status,

            # Financial metrics
            total_shares_outstanding=portfolio_data.total_shares_outstanding,
            minimum_investment=portfolio_data.minimum_investment,

            # Risk and constraints
            risk_level=portfolio_data.risk_level,
            max_individual_weight=portfolio_data.max_individual_weight,
            min_individual_weight=portfolio_data.min_individual_weight,
            max_sector_weight=portfolio_data.max_sector_weight,
            max_country_weight=portfolio_data.max_country_weight,
            cash_target_percentage=portfolio_data.cash_target_percentage,

            # Evaluation and calculation context
            calendar=portfolio_data.calendar,
            business_day_convention=portfolio_data.business_day_convention,
            last_rebalance_date=portfolio_data.last_rebalance_date,

            # Fees and expenses
            management_fee=portfolio_data.management_fee,
            performance_fee=portfolio_data.performance_fee,
            expense_ratio=portfolio_data.expense_ratio,

            # Operational fields
            is_active=portfolio_data.is_active,
            is_locked=portfolio_data.is_locked,
            allow_fractional_shares=portfolio_data.allow_fractional_shares,
            auto_rebalance_enabled=portfolio_data.auto_rebalance_enabled,

            # Metadata and configuration
            custom_fields=portfolio_data.custom_fields,
            compliance_rules=portfolio_data.compliance_rules,
            tags=portfolio_data.tags,

            # Manager/Administrator information
            portfolio_manager=portfolio_data.portfolio_manager,
            administrator=portfolio_data.administrator,
            custodian=portfolio_data.custodian,

            version=1
        )
        self.db.add(portfolio)
        return portfolio

    def create_constituents(self, portfolio_id: int, validated_constituents: List[Dict[str, Any]],
                            asset_class: AssetClassEnum) -> List[Constituent]:
        """Create constituent records"""
        new_constituents = []
        for data in validated_constituents:
            constituent = Constituent(
                portfolio_id=portfolio_id,
                asset_id=data["asset_id"],
                asset_class=asset_class,
                currency=data["currency"],
                weight=data["weight"],
                target_weight=data["target_weight"],
                units=data["units"],
                market_price=data["market_price"],
                is_active=data["is_active"]
            )
            self.db.add(constituent)
            new_constituents.append(constituent)
        return new_constituents

    def remove_constituents(self, portfolio_id: int) -> None:
        """Remove all constituents for a portfolio"""
        self.db.query(Constituent).filter(
            Constituent.portfolio_id == portfolio_id
        ).delete()

    def delete_portfolio(self, portfolio_id: int) -> bool:
        """Delete portfolio and constituents"""
        portfolio = self.get_by_id(portfolio_id)
        if not portfolio:
            return False

        self.remove_constituents(portfolio_id)
        self.db.delete(portfolio)
        return True
