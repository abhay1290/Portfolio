import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from portfolio.src.api.dependencies import EquityServiceClient, FixedIncomeServiceClient
from portfolio.src.api.schemas.constituent_schema import (
    PortfolioBondRequest, PortfolioBondResponse,
    PortfolioEquityRequest, PortfolioEquityResponse
)
from portfolio.src.api.schemas.portfolio_schema import (PortfolioPerformanceResponse, PortfolioRequest,
                                                        PortfolioResponse, PortfolioSummaryResponse)
from portfolio.src.database import get_db
from portfolio.src.model.Portfolio import Portfolio, portfolio_bond_association, portfolio_equity_association
from portfolio.src.model.enums import BusinessDayConventionEnum, CalendarEnum, WeightingMethodologyEnum
from portfolio.src.model.enums.PortfolioStatusEnum import PortfolioStatusEnum
from portfolio.src.model.enums.RebalanceFrequencyEnum import RebalanceFrequencyEnum

logger = logging.getLogger(__name__)


# noinspection PyTypeChecker
class PortfolioService:
    """
    Service class for portfolio construction and management.
    Coordinates with equity and fixed income services for instrument validation and data.
    """

    def __init__(self,
                 equity_client: EquityServiceClient,
                 fixed_income_client: FixedIncomeServiceClient):
        self.equity_client = equity_client
        self.fixed_income_client = fixed_income_client
        self.logger = logging.getLogger(__name__)

    # Portfolio CRUD Operations

    async def create_portfolio(self,
                               portfolio_data: PortfolioRequest,
                               db: Session,
                               user_token: str) -> PortfolioResponse:
        """
        Create a new portfolio with validated constituents.
        """
        try:
            # Check if portfolio symbol already exists
            existing = db.query(Portfolio).filter(
                portfolio_data.symbol == Portfolio.symbol
            ).first()
            if existing:
                raise ValueError(f"Portfolio with symbol {portfolio_data.symbol} already exists")

            # Validate constituents first
            validated_equities = await self._validate_equities(
                portfolio_data.equity_ids, user_token
            )
            validated_bonds = await self._validate_bonds(
                portfolio_data.bond_ids, user_token
            )

            # Validate weights
            self._validate_portfolio_weights(
                validated_equities + validated_bonds
            )

            # Create portfolio entity
            portfolio = Portfolio(
                symbol=portfolio_data.symbol,
                name=portfolio_data.name,
                description=portfolio_data.description,
                inception_date=portfolio_data.inception_date or date.today(),
                portfolio_type=portfolio_data.portfolio_type,
                status=portfolio_data.status or PortfolioStatusEnum.ACTIVE,
                base_currency=portfolio_data.base_currency,
                asset_class=portfolio_data.asset_class,
                weighting_methodology=portfolio_data.weighting_methodology,
                rebalance_frequency=portfolio_data.rebalance_frequency or RebalanceFrequencyEnum.MONTHLY,
                benchmark_symbol=portfolio_data.benchmark_symbol,
                strategy_description=portfolio_data.strategy_description,
                calendar=portfolio_data.calendar or CalendarEnum.TARGET,
                business_day_convention=portfolio_data.business_day_convention or BusinessDayConventionEnum.FOLLOWING,
                allow_fractional_shares=portfolio_data.allow_fractional_shares or True,
                auto_rebalance_enabled=portfolio_data.auto_rebalance_enabled or False,
                created_at=datetime.now(),
                version=1
            )

            db.add(portfolio)
            db.flush()  # Get the portfolio ID

            # Add constituents
            portfolio_equities = await self._create_portfolio_equities(
                portfolio.id, validated_equities, db
            )
            portfolio_bonds = await self._create_portfolio_bonds(
                portfolio.id, validated_bonds, db
            )

            # Calculate initial market value and NAV
            total_market_value = await self._calculate_total_market_value(
                portfolio_equities, portfolio_bonds, user_token
            )
            portfolio.total_market_value = total_market_value
            portfolio.nav_per_share = self._calculate_nav_per_share(portfolio)

            # Set next rebalance date
            portfolio.next_rebalance_date = self._calculate_next_rebalance_date(
                portfolio.rebalance_frequency,
                datetime.now().date()
            )

            db.commit()

            self.logger.info(f"Portfolio created successfully: {portfolio.symbol} (ID: {portfolio.id})")

            return await self._build_portfolio_response(portfolio, db, user_token)

        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating portfolio: {str(e)}", exc_info=True)
            raise

    async def get_portfolio(self,
                            portfolio_id: int,
                            db: Session,
                            user_token: str) -> Optional[PortfolioResponse]:
        """
        Retrieve a portfolio by ID with all constituents.
        """
        try:
            portfolio = db.query(Portfolio).filter(portfolio_id == Portfolio.id).first()
            if not portfolio:
                return None

            return await self._build_portfolio_response(portfolio, db, user_token)

        except Exception as e:
            self.logger.error(f"Error retrieving portfolio {portfolio_id}: {str(e)}", exc_info=True)
            raise

    async def update_portfolio(self,
                               portfolio_id: int,
                               portfolio_data: PortfolioRequest,
                               db: Session,
                               user_token: str) -> Optional[PortfolioResponse]:
        """
        Update an existing portfolio and its constituents.
        """
        try:
            portfolio = db.query(Portfolio).filter(portfolio_id == Portfolio.id).first()
            if not portfolio:
                return None

            # Check if updating to a symbol that already exists
            if portfolio_data.symbol and portfolio_data.symbol != portfolio.symbol:
                existing = db.query(Portfolio).filter(
                    portfolio_data.symbol == Portfolio.symbol,
                    portfolio_id != Portfolio.id
                ).first()
                if existing:
                    raise ValueError(f"Portfolio with symbol {portfolio_data.symbol} already exists")

            # Update portfolio fields
            update_fields = portfolio_data.model_dump(exclude={'equity_ids', 'bond_ids'}, exclude_unset=True)
            for field, value in update_fields.items():
                if value is not None:
                    setattr(portfolio, field, value)

            portfolio.updated_at = datetime.now()
            portfolio.version += 1

            # Update constituents if provided
            if portfolio_data.equity_ids is not None or portfolio_data.bond_ids is not None:
                await self._update_portfolio_constituents(
                    portfolio_id, portfolio_data, db, user_token
                )

            # Recalculate market value and NAV
            portfolio_equities = db.query(portfolio_equity_association).filter(
                portfolio_id == portfolio_equity_association.portfolio_id
            ).all()
            portfolio_bonds = db.query(portfolio_bond_association).filter(
                portfolio_id == portfolio_bond_association.portfolio_id
            ).all()

            total_market_value = await self._calculate_total_market_value(
                portfolio_equities, portfolio_bonds, user_token
            )
            portfolio.total_market_value = total_market_value
            portfolio.nav_per_share = self._calculate_nav_per_share(portfolio)

            db.commit()

            self.logger.info(f"Portfolio updated successfully: {portfolio.symbol} (ID: {portfolio.id})")

            return await self._build_portfolio_response(portfolio, db, user_token)

        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating portfolio {portfolio_id}: {str(e)}", exc_info=True)
            raise

    async def delete_portfolio(self, portfolio_id: int, db: Session) -> bool:
        """
        Delete a portfolio and all its constituents.
        """
        try:
            portfolio = db.query(Portfolio).filter(portfolio_id == Portfolio.id).first()
            if not portfolio:
                return False

            # Delete constituents first (cascade should handle this, but being explicit)
            db.query(portfolio_equity_association).filter(
                portfolio_id == portfolio_equity_association.portfolio_id).delete()
            db.query(portfolio_bond_association).filter(
                portfolio_id == portfolio_bond_association.portfolio_id).delete()

            # Delete portfolio
            db.delete(portfolio)
            db.commit()

            self.logger.info(f"Portfolio deleted successfully: ID {portfolio_id}")
            return True

        except Exception as e:
            db.rollback()
            self.logger.error(f"Error deleting portfolio {portfolio_id}: {str(e)}", exc_info=True)
            raise

    # Portfolio Management Operations

    async def rebalance_portfolio(self,
                                  portfolio_id: int,
                                  db: Session,
                                  user_token: str) -> PortfolioResponse:
        """
        Rebalance portfolio to target weights.
        """
        try:
            portfolio = db.query(Portfolio).filter(portfolio_id == Portfolio.id).first()
            if not portfolio:
                raise ValueError(f"Portfolio {portfolio_id} not found")

            if not portfolio.auto_rebalance_enabled:
                raise ValueError(f"Auto-rebalance is disabled for portfolio {portfolio_id}")

            # Get current constituents
            equities = db.query(portfolio_equity_association).filter(
                portfolio_id == portfolio_equity_association.portfolio_id
            ).all()
            bonds = db.query(portfolio_bond_association).filter(
                portfolio_id == portfolio_bond_association.portfolio_id
            ).all()

            # Calculate new weights based on methodology
            await self._rebalance_constituents(equities, bonds, portfolio.weighting_methodology)

            # Update rebalance timestamp and weights
            rebalance_time = datetime.now()
            for equity in equities:
                equity.last_rebalanced_at = rebalance_time
                equity.weight = equity.target_weight

            for bond in bonds:
                bond.last_rebalanced_at = rebalance_time
                bond.weight = bond.target_weight

            # Update portfolio metadata
            portfolio.last_rebalance_date = rebalance_time.date()
            portfolio.next_rebalance_date = self._calculate_next_rebalance_date(
                portfolio.rebalance_frequency,
                rebalance_time.date()
            )
            portfolio.updated_at = rebalance_time

            # Recalculate market value and NAV
            total_market_value = await self._calculate_total_market_value(
                equities, bonds, user_token
            )
            portfolio.total_market_value = total_market_value
            portfolio.nav_per_share = self._calculate_nav_per_share(portfolio)

            db.commit()

            self.logger.info(f"Portfolio rebalanced successfully: {portfolio.symbol} (ID: {portfolio.id})")

            return await self._build_portfolio_response(portfolio, db, user_token)

        except Exception as e:
            db.rollback()
            self.logger.error(f"Error rebalancing portfolio {portfolio_id}: {str(e)}", exc_info=True)
            raise

    async def get_portfolio_summary(self,
                                    portfolio_id: int,
                                    db: Session) -> Optional[PortfolioSummaryResponse]:
        """
        Get portfolio summary information without full constituent details.
        """
        try:
            portfolio = db.query(Portfolio).filter(portfolio_id == Portfolio.id).first()
            if not portfolio:
                return None

            # Count constituents
            equity_count = db.query(portfolio_equity_association).filter(
                portfolio_id == portfolio_equity_association.portfolio_id
            ).count()

            bond_count = db.query(portfolio_bond_association).filter(
                portfolio_id == portfolio_bond_association.portfolio_id
            ).count()

            return PortfolioSummaryResponse(
                id=portfolio.id,
                symbol=portfolio.symbol,
                name=portfolio.name,
                portfolio_type=portfolio.portfolio_type.name,
                base_currency=portfolio.base_currency.name,
                asset_class=portfolio.asset_class.name,
                status=portfolio.status.name,
                total_market_value=portfolio.total_market_value,
                nav_per_share=portfolio.nav_per_share,
                equity_count=equity_count,
                bond_count=bond_count,
                last_updated=portfolio.updated_at or portfolio.created_at,
                last_rebalance_date=portfolio.last_rebalance_date,
                next_rebalance_date=portfolio.next_rebalance_date
            )

        except Exception as e:
            self.logger.error(f"Error getting portfolio summary {portfolio_id}: {str(e)}", exc_info=True)
            raise

    async def get_portfolio_performance(self,
                                        portfolio_id: int,
                                        db: Session) -> Optional[PortfolioPerformanceResponse]:
        """
        Get portfolio performance metrics.
        """
        try:
            portfolio = db.query(Portfolio).filter(portfolio_id == Portfolio.id).first()
            if not portfolio:
                return None

            # TODO: Implement actual performance calculation logic
            # This would typically involve:
            # 1. Getting historical NAVs
            # 2. Calculating returns over different periods
            # 3. Comparing to benchmark
            # 4. Calculating risk metrics

            return PortfolioPerformanceResponse(
                portfolio_id=portfolio.id,
                symbol=portfolio.symbol,
                inception_to_date_return=None,
                year_to_date_return=None,
                one_year_return=None,
                three_year_annualized=None,
                five_year_annualized=None,
                volatility=None,
                sharpe_ratio=None,
                max_drawdown=None,
                benchmark_symbol=portfolio.benchmark_symbol,
                benchmark_returns=None,
                last_updated=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error getting portfolio performance {portfolio_id}: {str(e)}", exc_info=True)
            raise

    async def add_constituents(self,
                               portfolio_id: int,
                               equity_requests: List[PortfolioEquityRequest],
                               bond_requests: List[PortfolioBondRequest],
                               db: Session,
                               user_token: str) -> PortfolioResponse:
        """
        Add new constituents to an existing portfolio.
        """
        try:
            portfolio = db.query(Portfolio).filter(portfolio_id == Portfolio.id).first()
            if not portfolio:
                raise ValueError(f"Portfolio {portfolio_id} not found")

            # Validate new constituents
            validated_equities = await self._validate_equities(equity_requests, user_token)
            validated_bonds = await self._validate_bonds(bond_requests, user_token)

            # Add new constituents
            new_equities = await self._create_portfolio_equities(portfolio_id, validated_equities, db)
            new_bonds = await self._create_portfolio_bonds(portfolio_id, validated_bonds, db)

            # Recalculate weights to maintain portfolio balance
            await self._adjust_weights_after_addition(portfolio_id, db)

            # Recalculate market value and NAV
            portfolio_equities = db.query(portfolio_equity_association).filter(
                portfolio_id == portfolio_equity_association.portfolio_id
            ).all()
            portfolio_bonds = db.query(portfolio_bond_association).filter(
                portfolio_id == portfolio_bond_association.portfolio_id
            ).all()

            total_market_value = await self._calculate_total_market_value(
                portfolio_equities, portfolio_bonds, user_token
            )
            portfolio.total_market_value = total_market_value
            portfolio.nav_per_share = self._calculate_nav_per_share(portfolio)
            portfolio.updated_at = datetime.now()

            db.commit()

            self.logger.info(
                f"Added {len(new_equities)} equities and {len(new_bonds)} bonds to portfolio {portfolio_id}")

            return await self._build_portfolio_response(portfolio, db, user_token)

        except Exception as e:
            db.rollback()
            self.logger.error(f"Error adding constituents to portfolio {portfolio_id}: {str(e)}", exc_info=True)
            raise

    # Private Helper Methods

    async def _validate_equities(self,
                                 equity_requests: List[PortfolioEquityRequest],
                                 user_token: str) -> List[Dict]:
        """
        Validate equity instruments exist and are accessible.
        """
        validated_equities = []

        for req in equity_requests:
            try:
                # Fetch equity details from equity service
                equity_data = await self.equity_client.get_equity_instrument(
                    str(req.equity_id), user_token
                )

                validated_equities.append({
                    "equity_id": req.equity_id,
                    "symbol": req.symbol or equity_data.get('symbol'),
                    "weight": req.weight,
                    "target_weight": req.target_weight or req.weight,
                    "units": req.units,
                    "currency": req.currency or equity_data.get('currency'),
                    "is_active": req.is_active if req.is_active is not None else True,
                    "instrument_data": equity_data
                })

            except Exception as e:
                self.logger.error(f"Failed to validate equity {req.equity_id}: {str(e)}")
                raise ValueError(f"Equity {req.equity_id} validation failed: {str(e)}")

        return validated_equities

    async def _validate_bonds(self,
                              bond_requests: List[PortfolioBondRequest],
                              user_token: str) -> List[Dict]:
        """
        Validate bond instruments exist and are accessible.
        """
        validated_bonds = []

        for req in bond_requests:
            try:
                # Fetch bond details from fixed income service
                bond_data = await self.fixed_income_client.get_fixed_income_instrument(
                    str(req.bond_id), user_token
                )

                validated_bonds.append({
                    "bond_id": req.bond_id,
                    "symbol": req.symbol or bond_data.get('symbol'),
                    "weight": req.weight,
                    "target_weight": req.target_weight or req.weight,
                    "units": req.units,
                    "currency": req.currency or bond_data.get('currency'),
                    "is_active": req.is_active if req.is_active is not None else True,
                    "instrument_data": bond_data
                })

            except Exception as e:
                self.logger.error(f"Failed to validate bond {req.bond_id}: {str(e)}")
                raise ValueError(f"Bond {req.bond_id} validation failed: {str(e)}")

        return validated_bonds

    def _validate_portfolio_weights(self, constituents: List[Dict]) -> None:
        """
        Validate that portfolio weights sum to approximately 1.0.
        """
        if not constituents:
            return

        total_weight = sum(Decimal(str(c["weight"])) for c in constituents)

        if not (Decimal("0.98") <= total_weight <= Decimal("1.02")):
            raise ValueError(f"Portfolio weights sum to {total_weight}, must be close to 1.0")

    async def _create_portfolio_equities(self,
                                         portfolio_id: int,
                                         validated_equities: List[Dict],
                                         db: Session) -> List[portfolio_equity_association]:
        """
        Create portfolio equity constituent records.
        """
        portfolio_equities = []

        for equity_data in validated_equities:
            portfolio_equity = portfolio_equity_association.insert().values(
                portfolio_id=portfolio_id,
                equity_id=equity_data["equity_id"],
                symbol=equity_data["symbol"],
                weight=equity_data["weight"],
                target_weight=equity_data["target_weight"],
                units=equity_data.get("units"),
                currency=equity_data["currency"],
                is_active=equity_data["is_active"],
                added_at=datetime.now()
            )
            db.execute(portfolio_equity)
            portfolio_equities.append(portfolio_equity)

        return portfolio_equities

    async def _create_portfolio_bonds(self,
                                      portfolio_id: int,
                                      validated_bonds: List[Dict],
                                      db: Session) -> List[portfolio_bond_association]:
        """
        Create portfolio bond constituent records.
        """
        portfolio_bonds = []

        for bond_data in validated_bonds:
            portfolio_bond = portfolio_bond_association.insert().values(
                portfolio_id=portfolio_id,
                bond_id=bond_data["bond_id"],
                symbol=bond_data["symbol"],
                weight=bond_data["weight"],
                target_weight=bond_data["target_weight"],
                units=bond_data.get("units"),
                currency=bond_data["currency"],
                is_active=bond_data["is_active"],
                added_at=datetime.now()
            )
            db.execute(portfolio_bond)
            portfolio_bonds.append(portfolio_bond)

        return portfolio_bonds

    async def _calculate_total_market_value(self,
                                            equities: List[portfolio_equity_association],
                                            bonds: List[portfolio_bond_association],
                                            user_token: str, db: Session = get_db()) -> Optional[Decimal]:
        """
        Calculate total market value of portfolio constituents.
        """
        try:
            total_value = Decimal("0")

            # Calculate equity values
            for equity in equities:
                if equity.units:
                    # Get current price from equity service
                    equity_data = await self.equity_client.get_equity_instrument(
                        str(equity.equity_id), user_token
                    )
                    current_price = Decimal(str(equity_data.get("current_price", 0)))
                    market_value = equity.units * current_price
                    db.execute(
                        portfolio_equity_association.update()
                        .where(
                            and_(
                                portfolio_equity_association.c.portfolio_id == equity.portfolio_id,
                                portfolio_equity_association.c.equity_id == equity.equity_id
                            )
                        )
                        .values(market_value=market_value)
                    )
                    total_value += market_value

            # Calculate bond values
            for bond in bonds:
                if bond.units:
                    # Get current price from fixed income service
                    bond_data = await self.fixed_income_client.get_fixed_income_instrument(
                        str(bond.bond_id), user_token
                    )
                    current_price = Decimal(str(bond_data.get("current_price", 0)))
                    market_value = bond.units * current_price
                    db.execute(
                        portfolio_bond_association.update()
                        .where(
                            and_(
                                portfolio_bond_association.c.portfolio_id == bond.portfolio_id,
                                portfolio_bond_association.c.bond_id == bond.bond_id
                            )
                        )
                        .values(market_value=market_value)
                    )
                    total_value += market_value

            return total_value

        except Exception as e:
            self.logger.error(f"Error calculating market value: {str(e)}")
            return None

    def _calculate_nav_per_share(self, portfolio: Portfolio) -> Optional[Decimal]:
        """
        Calculate NAV per share.
        """
        if portfolio.total_market_value and portfolio.total_shares_outstanding:
            return Decimal(portfolio.total_market_value) / Decimal(portfolio.total_shares_outstanding)
        return None

    def _calculate_next_rebalance_date(self,
                                       frequency: RebalanceFrequencyEnum,
                                       from_date: date) -> date:
        """
        Calculate next rebalance date based on frequency.
        """
        if frequency == RebalanceFrequencyEnum.DAILY:
            return from_date
        elif frequency == RebalanceFrequencyEnum.WEEKLY:
            return from_date + timedelta(days=7)
        elif frequency == RebalanceFrequencyEnum.MONTHLY:
            # Move to same day next month (handle end of month cases)
            try:
                return from_date.replace(month=from_date.month + 1)
            except ValueError:
                # Handle month overflow (December -> January next year)
                if from_date.month == 12:
                    return from_date.replace(year=from_date.year + 1, month=1)
        elif frequency == RebalanceFrequencyEnum.QUARTERLY:
            # Move to same day next quarter
            quarter = (from_date.month - 1) // 3 + 1
            next_quarter_month = quarter * 3 + 1
            next_quarter_year = from_date.year
            if next_quarter_month > 12:
                next_quarter_month -= 12
                next_quarter_year += 1
            try:
                return from_date.replace(year=next_quarter_year, month=next_quarter_month)
            except ValueError:
                # Handle invalid day for next month (e.g., 31st to 30th)
                last_day = (from_date.replace(month=next_quarter_month + 1, day=1) - timedelta(days=1))
                return last_day
        elif frequency == RebalanceFrequencyEnum.ANNUALLY:
            try:
                return from_date.replace(year=from_date.year + 1)
            except ValueError:
                # Handle leap year (Feb 29)
                return from_date.replace(year=from_date.year + 1, month=2, day=28)
        elif frequency == RebalanceFrequencyEnum.NEVER:
            return None
        else:
            return from_date

    async def _build_portfolio_response(self,
                                        portfolio: Portfolio,
                                        db: Session,
                                        user_token: str) -> PortfolioResponse:
        """
        Build complete portfolio response with constituents.
        """
        # Get constituents
        portfolio_equities = db.query(portfolio_equity_association).filter(
            portfolio_equity_association.c.portfolio_id == portfolio.id
        ).all()

        portfolio_bonds = db.query(portfolio_bond_association).filter(
            portfolio_bond_association.c.portfolio_id == portfolio.id
        ).all()

        # Build response objects
        equity_responses = [
            PortfolioEquityResponse(
                equity_id=pe.equity_id,
                symbol=pe.symbol,
                weight=pe.weight,
                target_weight=pe.target_weight,
                currency=pe.currency,
                is_active=pe.is_active,
                market_value=pe.market_value,
                added_at=pe.added_at,
                last_rebalanced_at=pe.last_rebalanced_at,
                outstanding_shares=pe.units
            ) for pe in portfolio_equities
        ]

        bond_responses = [
            PortfolioBondResponse(
                bond_id=pb.bond_id,
                symbol=pb.symbol,
                weight=pb.weight,
                target_weight=pb.target_weight,
                currency=pb.currency,
                is_active=pb.is_active,
                market_value=pb.market_value,
                added_at=pb.added_at,
                last_rebalanced_at=pb.last_rebalanced_at,
                outstanding_shares=pb.units
            ) for pb in portfolio_bonds
        ]

        return PortfolioResponse(
            id=portfolio.id,
            symbol=portfolio.symbol,
            name=portfolio.name,
            description=portfolio.description,
            inception_date=portfolio.inception_date,
            portfolio_type=portfolio.portfolio_type,
            status=portfolio.status,
            base_currency=portfolio.base_currency,
            asset_class=portfolio.asset_class,
            weighting_methodology=portfolio.weighting_methodology,
            rebalance_frequency=portfolio.rebalance_frequency,
            benchmark_symbol=portfolio.benchmark_symbol,
            strategy_description=portfolio.strategy_description,
            calendar=portfolio.calendar,
            business_day_convention=portfolio.business_day_convention,
            allow_fractional_shares=portfolio.allow_fractional_shares,
            auto_rebalance_enabled=portfolio.auto_rebalance_enabled,
            created_at=portfolio.created_at,
            updated_at=portfolio.updated_at,
            version=portfolio.version,
            total_market_value=portfolio.total_market_value,
            nav_per_share=portfolio.nav_per_share,
            last_rebalance_date=portfolio.last_rebalance_date,
            next_rebalance_date=portfolio.next_rebalance_date,
            equity_ids=[pe.equity_id for pe in portfolio_equities],
            bond_ids=[pb.bond_id for pb in portfolio_bonds],
            equities=equity_responses,
            bonds=bond_responses
        )

    async def _update_portfolio_constituents(self,
                                             portfolio_id: int,
                                             portfolio_data: PortfolioRequest,
                                             db: Session,
                                             user_token: str) -> None:
        """
        Update portfolio constituents (replace existing).
        """
        # Remove existing constituents
        db.execute(
            portfolio_equity_association.delete().where(
                portfolio_equity_association.c.portfolio_id == portfolio_id
            )
        )
        db.execute(
            portfolio_bond_association.delete().where(
                portfolio_bond_association.c.portfolio_id == portfolio_id
            )
        )

        # Add new constituents
        if portfolio_data.equity_ids:
            validated_equities = await self._validate_equities(
                portfolio_data.equity_ids, user_token
            )
            await self._create_portfolio_equities(portfolio_id, validated_equities, db)

        if portfolio_data.bond_ids:
            validated_bonds = await self._validate_bonds(
                portfolio_data.bond_ids, user_token
            )
            await self._create_portfolio_bonds(portfolio_id, validated_bonds, db)

    async def _rebalance_constituents(self,
                                      equities: List[portfolio_equity_association],
                                      bonds: List[portfolio_bond_association],
                                      methodology: WeightingMethodologyEnum) -> None:
        """
        Apply rebalancing logic based on weighting methodology.
        """
        if methodology == WeightingMethodologyEnum.EQUALLY_WEIGHTED:
            total_constituents = len(equities) + len(bonds)
            if total_constituents > 0:
                equal_weight = Decimal("1") / Decimal(str(total_constituents))

                for equity in equities:
                    equity.target_weight = equal_weight

                for bond in bonds:
                    bond.target_weight = equal_weight

        elif methodology == WeightingMethodologyEnum.MARKET_CAP_WEIGHTED:
            # Calculate total market value
            total_market_value = sum(
                [e.market_value for e in equities if e.market_value] +
                [b.market_value for b in bonds if b.market_value]
            )

            if total_market_value > 0:
                # Update equity weights
                for equity in equities:
                    if equity.market_value:
                        equity.target_weight = Decimal(equity.market_value) / Decimal(total_market_value)

                # Update bond weights
                for bond in bonds:
                    if bond.market_value:
                        bond.target_weight = Decimal(bond.market_value) / Decimal(total_market_value)

        elif methodology == WeightingMethodologyEnum.FIXED_WEIGHTED:
            # No change needed - use existing target weights
            pass

    async def _adjust_weights_after_addition(self,
                                             portfolio_id: int,
                                             db: Session) -> None:
        """
        Adjust weights proportionally after adding new constituents.
        """
        # Get all constituents
        equities = db.query(portfolio_equity_association).filter(
            portfolio_id == portfolio_equity_association.c.portfolio_id
        ).all()
        bonds = db.query(portfolio_bond_association).filter(
            portfolio_id == portfolio_bond_association.c.portfolio_id
        ).all()

        total_weight = sum(e.weight for e in equities) + sum(b.weight for b in bonds)

        if total_weight > 0:
            # Scale down existing weights proportionally
            scale_factor = Decimal("1") / Decimal(total_weight)

            for equity in equities:
                new_weight = Decimal(equity.weight) * scale_factor
                db.execute(
                    portfolio_equity_association.update()
                    .where(
                        and_(
                            portfolio_equity_association.c.portfolio_id == equity.portfolio_id,
                            portfolio_equity_association.c.equity_id == equity.equity_id
                        )
                    )
                    .values(weight=new_weight)
                )

            for bond in bonds:
                new_weight = Decimal(bond.weight) * scale_factor
                db.execute(
                    portfolio_bond_association.update()
                    .where(
                        and_(
                            portfolio_bond_association.c.portfolio_id == bond.portfolio_id,
                            portfolio_bond_association.c.bond_id == bond.bond_id
                        )
                    )
                    .values(weight=new_weight)
                )
