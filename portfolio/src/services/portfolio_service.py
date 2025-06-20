import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from QuantLib import Days, Months, Period, Weeks, Years
from fastapi import Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status

from portfolio.src.api.dependencies import EquityServiceClient, FixedIncomeServiceClient, get_equity_service, \
    get_fixed_income_service
from portfolio.src.api.schemas.constituent_schema import (
    PortfolioBondRequest, PortfolioBondResponse, PortfolioEquityRequest, PortfolioEquityResponse
)
from portfolio.src.api.schemas.portfolio_schema import (
    PortfolioPerformanceResponse, PortfolioRequest,
    PortfolioResponse, PortfolioSummaryResponse
)
from portfolio.src.database import get_db
from portfolio.src.model.Constituent import Constituent
from portfolio.src.model.Portfolio import Portfolio
from portfolio.src.model.PortfolioVersion import PortfolioVersion
from portfolio.src.model.enums import (
    AssetClassEnum, BusinessDayConventionEnum, CalendarEnum,
    RebalanceFrequencyEnum,
    VersionOperationTypeEnum, WeightingMethodologyEnum
)
from portfolio.src.services.PortfolioVersioningManager import PortfolioVersioningManager
from portfolio.src.services.constituent_price_service import PriceService
from portfolio.src.services.portfolio_calculator import PortfolioCalculator
from portfolio.src.services.portfolio_repository import PortfolioRepository
from portfolio.src.services.portfolio_service_config import PortfolioServiceConfig
from portfolio.src.services.portfolio_validator import PortfolioValidator
from portfolio.src.utils.Exceptions import ConstituentValidationError, PortfolioExistsError, PortfolioNotFoundError, \
    PortfolioValidationError
from portfolio.src.utils.quantlib_mapper import from_ql_date, to_ql_business_day_convention, to_ql_calendar, to_ql_date

logger = logging.getLogger(__name__)


class PortfolioService:
    """
    Service class for portfolio construction and management.
    Coordinates with equity and fixed income services for instrument validation and data.
    """

    def __init__(
            self,
            db: Session = Depends(get_db),
            equity_client: EquityServiceClient = Depends(get_equity_service),
            fixed_income_client: FixedIncomeServiceClient = Depends(get_fixed_income_service),
            config: Optional[PortfolioServiceConfig] = None
    ):
        self.config = config or PortfolioServiceConfig()
        self.db = db
        self.repository = PortfolioRepository(db)
        self.validator = PortfolioValidator(self.config)
        self.calculator = PortfolioCalculator(self.config)
        self.price_service = PriceService(equity_client, fixed_income_client, self.config)
        self.versioning_manager = PortfolioVersioningManager(db)
        self.logger = logger
        self.executor = ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS)

    async def create_portfolio(self, portfolio_data: PortfolioRequest, user_token: str) -> PortfolioResponse:
        """Create a new portfolio with validated constituents"""
        try:
            # 1. Pre-validation
            await self.validator.validate_creation_request(portfolio_data)

            # 2. Check for existing portfolio
            await self._check_portfolio_existence(portfolio_data)

            # 3. Validate and process constituents
            validated_equities, validated_bonds = await self._process_constituents(portfolio_data, user_token)

            # 4. Create portfolio in transaction
            portfolio, all_constituents = await self._create_portfolio_and_constituents(
                portfolio_data, validated_equities, validated_bonds
            )

            # 5. Calculate and update metrics
            portfolio = await self._update_portfolio_metrics(portfolio, all_constituents, user_token)

            # 6. Create version and finalize
            portfolio = await self._finalize_portfolio_creation(portfolio, user_token)

            # 7. Commit transaction
            self.db.commit()

            return await self._build_portfolio_response(portfolio, user_token)

        except (PortfolioValidationError, ConstituentValidationError, PortfolioExistsError) as e:
            self.db.rollback()
            self.logger.warning(f"Portfolio creation validation failed: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error creating portfolio: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error creating portfolio: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def get_portfolio(self, portfolio_id: int, user_token: str) -> Optional[PortfolioResponse]:
        """Retrieve a portfolio by ID with all constituents"""
        try:
            portfolio = self.repository.get_by_id(portfolio_id)
            if not portfolio:
                return None

            return await self._build_portfolio_response(portfolio, user_token)

        except SQLAlchemyError as e:
            self.logger.error(f"Database error retrieving portfolio {portfolio_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            self.logger.error(f"Error retrieving portfolio {portfolio_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def update_portfolio(self, portfolio_id: int, portfolio_data: PortfolioRequest,
                               user_token: str, change_reason: str = None) -> Optional[PortfolioResponse]:
        """Update an existing portfolio and its constituents"""
        try:
            # 1. Get and validate existing portfolio
            portfolio = self.repository.get_by_id(portfolio_id)
            if not portfolio:
                raise PortfolioNotFoundError(f"Portfolio with ID {portfolio_id} not found")

            if portfolio.is_locked:
                raise PortfolioValidationError("Portfolio is locked and cannot be modified")

            # 2. Pre-validation
            await self.validator.validate_update_request(portfolio_data, portfolio)

            # 3. Validate and process constituents if provided
            validated_equities, validated_bonds = await self._process_update_constituents(
                portfolio_data, user_token
            )

            # 4. Update portfolio in transaction
            updated_portfolio, all_constituents = await self._update_portfolio_and_constituents(
                portfolio, portfolio_data, validated_equities, validated_bonds
            )

            # 5. Calculate and update metrics
            if all_constituents:  # Only update if constituents were modified
                updated_portfolio = await self._update_portfolio_metrics(
                    updated_portfolio, all_constituents, user_token
                )

            # 6. Create version and finalize
            updated_portfolio = await self._finalize_portfolio_update(
                updated_portfolio, user_token, change_reason
            )

            # 7. Commit transaction
            self.db.commit()

            return await self._build_portfolio_response(updated_portfolio, user_token)

        except (PortfolioValidationError, ConstituentValidationError, PortfolioNotFoundError) as e:
            self.db.rollback()
            self.logger.warning(f"Portfolio update validation failed: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error updating portfolio: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred during portfolio update"
            )
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error updating portfolio: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def delete_portfolio(self, portfolio_id: int) -> bool:
        """Delete a portfolio and all its constituents"""
        try:
            result = self.repository.delete_portfolio(portfolio_id)
            if result:
                self.db.commit()
            return result

        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error deleting portfolio {portfolio_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error deleting portfolio {portfolio_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def get_portfolio_summary(self, portfolio_id: int) -> Optional[PortfolioSummaryResponse]:
        """Get portfolio summary information without full constituent details"""
        try:
            portfolio = self.repository.get_by_id(portfolio_id)
            if not portfolio:
                return None

            equity_count = self.db.query(Constituent).filter(
                Constituent.portfolio_id == portfolio_id,
                Constituent.asset_class == AssetClassEnum.EQUITY,
                Constituent.is_active == True
            ).count()

            bond_count = self.db.query(Constituent).filter(
                Constituent.portfolio_id == portfolio_id,
                Constituent.asset_class == AssetClassEnum.FIXED_INCOME,
                Constituent.is_active == True
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    # Private Helper Methods

    async def _check_portfolio_existence(self, portfolio_data: PortfolioRequest) -> None:
        """Check if portfolio already exists"""
        if self.repository.exists(portfolio_data.id, portfolio_data.symbol):
            raise PortfolioExistsError("Portfolio with this ID or symbol already exists")

    async def _process_constituents(self, portfolio_data: PortfolioRequest,
                                    user_token: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Validate and process portfolio constituents"""
        # Concurrent validation
        equity_task = self._validate_equities(portfolio_data.equities or [], user_token)
        bond_task = self._validate_bonds(portfolio_data.bonds or [], user_token)

        validated_equities, validated_bonds = await asyncio.gather(
            equity_task, bond_task, return_exceptions=True
        )

        # Handle validation exceptions
        if isinstance(validated_equities, Exception):
            raise ConstituentValidationError(f"Equity validation failed: {str(validated_equities)}")
        if isinstance(validated_bonds, Exception):
            raise ConstituentValidationError(f"Bond validation failed: {str(validated_bonds)}")

        # Validate weights
        self.validator.validate_portfolio_weights(validated_equities + validated_bonds)

        return validated_equities, validated_bonds

    async def _process_update_constituents(self, portfolio_data: PortfolioRequest,
                                           user_token: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Validate and process portfolio constituents for update"""
        if portfolio_data.equities is None and portfolio_data.bonds is None:
            return [], []  # No constituent updates

        # Concurrent validation
        equity_task = self._validate_equities(portfolio_data.equities or [], user_token)
        bond_task = self._validate_bonds(portfolio_data.bonds or [], user_token)

        validated_equities, validated_bonds = await asyncio.gather(
            equity_task, bond_task, return_exceptions=True
        )

        # Handle validation exceptions
        if isinstance(validated_equities, Exception):
            raise ConstituentValidationError(f"Equity validation failed: {str(validated_equities)}")
        if isinstance(validated_bonds, Exception):
            raise ConstituentValidationError(f"Bond validation failed: {str(validated_bonds)}")

        # Validate weights if constituents are provided
        if portfolio_data.equities is not None or portfolio_data.bonds is not None:
            self.validator.validate_portfolio_weights(validated_equities + validated_bonds)

        return validated_equities, validated_bonds

    async def _create_portfolio_and_constituents(self, portfolio_data: PortfolioRequest,
                                                 validated_equities: List[Dict[str, Any]],
                                                 validated_bonds: List[Dict[str, Any]]) -> Tuple[
        Portfolio, List[Constituent]]:
        """Create portfolio and constituents in a transaction"""
        portfolio = self.repository.create_portfolio(portfolio_data)

        # Create constituents
        equity_constituents = self.repository.create_constituents(
            portfolio.id, validated_equities, AssetClassEnum.EQUITY
        )
        bond_constituents = self.repository.create_constituents(
            portfolio.id, validated_bonds, AssetClassEnum.FIXED_INCOME
        )

        self.db.flush()
        return portfolio, equity_constituents + bond_constituents

    async def _update_portfolio_and_constituents(self, portfolio: Portfolio,
                                                 portfolio_data: PortfolioRequest,
                                                 validated_equities: List[Dict[str, Any]],
                                                 validated_bonds: List[Dict[str, Any]]) -> Tuple[
        Portfolio, List[Constituent]]:
        """Update portfolio and constituents in a transaction"""
        # Update portfolio fields
        update_fields = portfolio_data.model_dump(
            exclude={'equities', 'bonds', 'id'},
            exclude_unset=True
        )
        for field, value in update_fields.items():
            setattr(portfolio, field, value)

        portfolio.updated_at = func.now()
        portfolio.version += 1

        # Only update constituents if they were provided in the request
        all_constituents = []
        if portfolio_data.equities is not None or portfolio_data.bonds is not None:
            # Remove existing constituents
            self.repository.remove_constituents(portfolio.id)

            # Add new constituents
            equity_constituents = self.repository.create_constituents(
                portfolio.id, validated_equities, AssetClassEnum.EQUITY
            )
            bond_constituents = self.repository.create_constituents(
                portfolio.id, validated_bonds, AssetClassEnum.FIXED_INCOME
            )
            all_constituents = equity_constituents + bond_constituents

        self.db.flush()
        return portfolio, all_constituents

    async def _update_portfolio_metrics(self, portfolio: Portfolio,
                                        constituents: List[Constituent],
                                        user_token: str) -> Portfolio:
        """Update portfolio with calculated metrics"""
        # Update market prices
        await self.price_service.update_market_prices(constituents, user_token)

        # Calculate metrics
        total_market_value = self.calculator.calculate_total_market_value(constituents)
        asset_allocation = self.calculator.calculate_asset_allocation(constituents)
        currency_exposure = self.calculator.calculate_currency_exposure(constituents)

        # Update portfolio
        portfolio.total_market_value = total_market_value
        portfolio.nav_per_share = self.calculator.calculate_nav_per_share(portfolio)
        portfolio.asset_allocation = asset_allocation
        portfolio.currency_exposure = currency_exposure
        self.db.flush()

        return portfolio

    async def _finalize_portfolio_creation(self, portfolio: Portfolio, user_token: str) -> Portfolio:
        """Finalize portfolio creation with versioning"""
        version = self.versioning_manager.create_version(
            portfolio=portfolio,
            operation_type=VersionOperationTypeEnum.CREATE,
            created_by=user_token,
            change_reason="Initial portfolio creation"
        )

        portfolio.current_version_id = version.id
        portfolio.version_hash = version.state_hash
        portfolio.next_rebalance_date = self._calculate_next_rebalance_date(
            portfolio.rebalance_frequency,
            portfolio.calendar,
            portfolio.business_day_convention,
            self._get_current_date()
        )

        self.db.flush()
        return portfolio

    async def _finalize_portfolio_update(self, portfolio: Portfolio, user_token: str,
                                         change_reason: str = None) -> Portfolio:
        """Finalize portfolio update with versioning"""
        version = self.versioning_manager.create_version(
            portfolio=portfolio,
            operation_type=VersionOperationTypeEnum.UPDATE,
            created_by=user_token,
            change_reason=change_reason or "Portfolio updated"
        )

        portfolio.current_version_id = version.id
        portfolio.version_hash = version.state_hash

        # Update rebalance date if frequency changed
        if hasattr(portfolio, 'rebalance_frequency'):
            portfolio.next_rebalance_date = self._calculate_next_rebalance_date(
                portfolio.rebalance_frequency,
                portfolio.calendar,
                portfolio.business_day_convention,
                self._get_current_date()
            )

        self.db.flush()
        return portfolio

    async def _validate_equities(self, equity_requests: List[PortfolioEquityRequest],
                                 user_token: str) -> List[Dict[str, Any]]:
        """Validate equity instruments exist and are accessible"""
        validated_equities = []

        for req in equity_requests:
            try:
                equity_data = await self.price_service.equity_client.get_equity_instrument(
                    equity_id=req.equity_id,
                    token=user_token)

                validated_equities.append({
                    "asset_id": req.equity_id,
                    "symbol": req.symbol or equity_data.get('symbol'),
                    "weight": req.weight,
                    "target_weight": req.target_weight or req.weight,
                    "units": req.units,
                    "currency": req.currency or equity_data.get('currency'),
                    "is_active": req.is_active if req.is_active is not None else True,
                    "market_price": equity_data.get('current_price', 0),
                    "instrument_data": equity_data
                })

            except Exception as e:
                self.logger.error(f"Failed to validate equity {req.equity_id}: {str(e)}")
                raise ConstituentValidationError(f"Equity {req.equity_id} validation failed: {str(e)}")

        return validated_equities

    async def _validate_bonds(self, bond_requests: List[PortfolioBondRequest],
                              user_token: str) -> List[Dict[str, Any]]:
        """Validate bond instruments exist and are accessible"""
        validated_bonds = []

        for req in bond_requests:
            try:
                bond_data = await self.price_service.fixed_income_client.get_fixed_income_instrument(
                    fixed_income_id=req.bond_id,
                    token=user_token)

                validated_bonds.append({
                    "asset_id": req.bond_id,
                    "symbol": req.symbol or bond_data.get('symbol'),
                    "weight": req.weight,
                    "target_weight": req.target_weight or req.weight,
                    "units": req.units,
                    "currency": req.currency or bond_data.get('currency'),
                    "is_active": req.is_active if req.is_active is not None else True,
                    "market_price": bond_data.get('current_price', 0),
                    "instrument_data": bond_data
                })

            except Exception as e:
                self.logger.error(f"Failed to validate bond {req.bond_id}: {str(e)}")
                raise ConstituentValidationError(f"Bond {req.bond_id} validation failed: {str(e)}")

        return validated_bonds

    async def _build_portfolio_response(self, portfolio: Portfolio, user_token: str) -> PortfolioResponse:
        """Build complete portfolio response with constituents"""
        try:
            # Eager load constituents with optimized query
            portfolio_with_constituents = self.repository.get_with_constituents(portfolio.id)

            if not portfolio_with_constituents:
                raise PortfolioNotFoundError(f"Portfolio with ID {portfolio.id} not found")

            # Process constituents in parallel
            equity_responses, bond_responses = await self._create_constituents_response(
                portfolio_with_constituents.constituents
            )

            # Build the comprehensive response
            return PortfolioResponse(
                # Base fields
                id=portfolio.id,
                symbol=portfolio.symbol,
                name=portfolio.name,
                description=portfolio.description,
                portfolio_type=portfolio.portfolio_type,
                base_currency=portfolio.base_currency,
                asset_class=portfolio.asset_class,

                # Lifecycle fields
                inception_date=portfolio.inception_date,
                termination_date=portfolio.termination_date,
                status=portfolio.status,

                # Methodology fields
                weighting_methodology=portfolio.weighting_methodology,
                rebalance_frequency=portfolio.rebalance_frequency,
                benchmark_symbol=portfolio.benchmark_symbol,
                strategy_description=portfolio.strategy_description,

                # Financial metrics
                minimum_investment=portfolio.minimum_investment,
                total_market_value=portfolio.total_market_value,
                nav_per_share=portfolio.nav_per_share,
                total_shares_outstanding=portfolio.total_shares_outstanding,
                last_nav_calculation_date=portfolio.last_nav_calculation_date,

                # Risk constraints
                risk_level=portfolio.risk_level,
                max_individual_weight=portfolio.max_individual_weight,
                min_individual_weight=portfolio.min_individual_weight,
                max_sector_weight=portfolio.max_sector_weight,
                max_country_weight=portfolio.max_country_weight,
                cash_target_percentage=portfolio.cash_target_percentage,

                # Calculation context
                calendar=portfolio.calendar,
                business_day_convention=portfolio.business_day_convention,
                last_rebalance_date=portfolio.last_rebalance_date,
                next_rebalance_date=portfolio.next_rebalance_date,

                # Fees
                management_fee=portfolio.management_fee,
                performance_fee=portfolio.performance_fee,
                expense_ratio=portfolio.expense_ratio,

                # Operational fields
                is_active=portfolio.is_active,
                is_locked=portfolio.is_locked,
                allow_fractional_shares=portfolio.allow_fractional_shares,
                auto_rebalance_enabled=portfolio.auto_rebalance_enabled,

                # Metadata
                custom_fields=portfolio.custom_fields,
                compliance_rules=portfolio.compliance_rules,
                tags=portfolio.tags,

                # Manager info
                portfolio_manager=portfolio.portfolio_manager,
                administrator=portfolio.administrator,
                custodian=portfolio.custodian,

                # Timestamps and versioning
                created_at=portfolio.created_at,
                updated_at=portfolio.updated_at,
                version=portfolio.version,
                version_hash=portfolio.version_hash,
                current_version_id=portfolio.current_version_id,

                # Constituents
                equities=equity_responses,
                bonds=bond_responses
            )
        except PortfolioNotFoundError as e:
            self.logger.error(f"Error building portfolio response: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Unexpected error building portfolio response: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error building portfolio response"
            )

    async def _create_constituents_response(self, constituents: List[Constituent]) -> Tuple[
        List[PortfolioEquityResponse], List[PortfolioBondResponse]]:
        """Process constituents into equity and bond responses"""
        equity_responses = []
        bond_responses = []

        for constituent in constituents:
            if constituent.asset_class == AssetClassEnum.EQUITY:
                equity_responses.append(self._build_equity_response(constituent))
            elif constituent.asset_class == AssetClassEnum.FIXED_INCOME:
                bond_responses.append(self._build_bond_response(constituent))

        return equity_responses, bond_responses

    @staticmethod
    def _build_equity_response(constituent: Constituent) -> PortfolioEquityResponse:
        """Build equity constituent response"""
        return PortfolioEquityResponse(
            equity_id=constituent.asset_id,
            symbol=constituent.symbol,
            weight=constituent.weight,
            target_weight=constituent.target_weight,
            currency=constituent.currency,
            is_active=constituent.is_active,
            market_value=constituent.market_value,
            added_at=constituent.added_at,
            last_rebalanced_at=constituent.last_rebalanced_at,
            outstanding_shares=constituent.units
        )

    @staticmethod
    def _build_bond_response(constituent: Constituent) -> PortfolioBondResponse:
        """Build bond constituent response"""
        return PortfolioBondResponse(
            bond_id=constituent.asset_id,
            symbol=constituent.symbol,
            weight=constituent.weight,
            target_weight=constituent.target_weight,
            currency=constituent.currency,
            is_active=constituent.is_active,
            market_value=constituent.market_value,
            added_at=constituent.added_at,
            last_rebalanced_at=constituent.last_rebalanced_at,
            outstanding_shares=constituent.units
        )

    @staticmethod
    def _calculate_next_rebalance_date(rebalance_frequency: RebalanceFrequencyEnum,
                                       calendar: CalendarEnum,
                                       business_day_convention: BusinessDayConventionEnum,
                                       from_date: date) -> date:
        """Calculate next rebalance date based on frequency"""
        last_rebalance_date = to_ql_date(from_date)
        calendar = to_ql_calendar(calendar)
        convention = to_ql_business_day_convention(business_day_convention)

        if rebalance_frequency == RebalanceFrequencyEnum.DAILY:
            period = Period(1, Days)
        elif rebalance_frequency == RebalanceFrequencyEnum.WEEKLY:
            period = Period(1, Weeks)
        elif rebalance_frequency == RebalanceFrequencyEnum.MONTHLY:
            period = Period(1, Months)
        elif rebalance_frequency == RebalanceFrequencyEnum.QUARTERLY:
            period = Period(3, Months)
        elif rebalance_frequency == RebalanceFrequencyEnum.ANNUALLY:
            period = Period(1, Years)
        else:
            return date.today()

        next_date = calendar.advance(last_rebalance_date, period, convention)
        return from_ql_date(next_date)

    @staticmethod
    def _get_current_date() -> date:
        """Get current UTC date"""
        return datetime.now(timezone.utc).date()

    # Additional Portfolio Operations

    async def add_constituents(self, portfolio_id: int,
                               equity_requests: List[PortfolioEquityRequest],
                               bond_requests: List[PortfolioBondRequest],
                               user_token: str) -> PortfolioResponse:
        """Add new constituents to an existing portfolio"""
        try:
            portfolio = self.repository.get_by_id(portfolio_id)
            if not portfolio:
                raise PortfolioNotFoundError(f"Portfolio {portfolio_id} not found")

            if portfolio.is_locked:
                raise PortfolioValidationError("Portfolio is locked and cannot be modified")

            validated_equities = await self._validate_equities(equity_requests, user_token)
            validated_bonds = await self._validate_bonds(bond_requests, user_token)

            # Create new constituents
            self.repository.create_constituents(portfolio_id, validated_equities, AssetClassEnum.EQUITY)
            self.repository.create_constituents(portfolio_id, validated_bonds, AssetClassEnum.FIXED_INCOME)

            # Adjust weights proportionally
            await self._adjust_weights(portfolio_id)

            # Get all constituents and update metrics
            constituents = self.db.query(Constituent).filter(
                Constituent.portfolio_id == portfolio_id
            ).all()

            portfolio = await self._update_portfolio_metrics(portfolio, constituents, user_token)

            # Create new version
            version = self.versioning_manager.create_version(
                portfolio=portfolio,
                operation_type=VersionOperationTypeEnum.ADD_CONSTITUENT,
                created_by=user_token,
                change_reason="Add Constituents"
            )

            portfolio.current_version_id = version.id
            portfolio.version_hash = version.state_hash
            portfolio.updated_at = func.now()

            self.db.commit()

            return await self._build_portfolio_response(portfolio, user_token)

        except (PortfolioValidationError, ConstituentValidationError, PortfolioNotFoundError) as e:
            self.db.rollback()
            self.logger.warning(f"Add constituents validation failed: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error adding constituents to portfolio {portfolio_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error adding constituents to portfolio {portfolio_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def remove_constituents(self, portfolio_id: int,
                                  equity_ids: List[int],
                                  bond_ids: List[int],
                                  user_token: str) -> PortfolioResponse:
        """Remove constituents from an existing portfolio"""
        try:
            portfolio = self.repository.get_by_id(portfolio_id)
            if not portfolio:
                raise PortfolioNotFoundError(f"Portfolio {portfolio_id} not found")

            if portfolio.is_locked:
                raise PortfolioValidationError("Portfolio is locked and cannot be modified")

            # Remove specific constituents
            if equity_ids:
                self.db.query(Constituent).filter(
                    Constituent.portfolio_id == portfolio_id,
                    Constituent.asset_class == AssetClassEnum.EQUITY,
                    Constituent.asset_id.in_(equity_ids)
                ).delete(synchronize_session=False)

            if bond_ids:
                self.db.query(Constituent).filter(
                    Constituent.portfolio_id == portfolio_id,
                    Constituent.asset_class == AssetClassEnum.FIXED_INCOME,
                    Constituent.asset_id.in_(bond_ids)
                ).delete(synchronize_session=False)

            # Adjust weights proportionally
            await self._adjust_weights(portfolio_id)

            # Get remaining constituents and update metrics
            constituents = self.db.query(Constituent).filter(
                Constituent.portfolio_id == portfolio_id
            ).all()

            portfolio = await self._update_portfolio_metrics(portfolio, constituents, user_token)

            # Create new version
            version = self.versioning_manager.create_version(
                portfolio=portfolio,
                operation_type=VersionOperationTypeEnum.REMOVE_CONSTITUENT,
                created_by=user_token,
                change_reason="Remove Constituents"
            )

            portfolio.current_version_id = version.id
            portfolio.version_hash = version.state_hash
            portfolio.updated_at = func.now()

            self.db.commit()

            return await self._build_portfolio_response(portfolio, user_token)

        except (PortfolioValidationError, PortfolioNotFoundError) as e:
            self.db.rollback()
            self.logger.warning(f"Remove constituents validation failed: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error removing constituents from portfolio {portfolio_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error removing constituents from portfolio {portfolio_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def rebalance_portfolio(self, portfolio_id: int, user_token: str) -> PortfolioResponse:
        """Rebalance portfolio to target weights"""
        try:
            portfolio = self.repository.get_by_id(portfolio_id)
            if not portfolio:
                raise PortfolioNotFoundError(f"Portfolio {portfolio_id} not found")

            if not portfolio.auto_rebalance_enabled:
                raise PortfolioValidationError(f"Auto-rebalance is disabled for portfolio {portfolio_id}")

            constituents = self.db.query(Constituent).filter(
                Constituent.portfolio_id == portfolio_id
            ).all()

            await self._rebalance_constituents(constituents, portfolio.weighting_methodology)

            rebalance_time = datetime.now(timezone.utc)
            for constituent in constituents:
                constituent.last_rebalanced_at = rebalance_time
                constituent.weight = constituent.target_weight

            portfolio.last_rebalance_date = rebalance_time.date()
            portfolio.next_rebalance_date = self._calculate_next_rebalance_date(
                portfolio.rebalance_frequency,
                portfolio.calendar,
                portfolio.business_day_convention,
                rebalance_time.date()
            )
            portfolio.updated_at = func.now()

            portfolio = await self._update_portfolio_metrics(portfolio, constituents, user_token)

            version = self.versioning_manager.create_version(
                portfolio=portfolio,
                operation_type=VersionOperationTypeEnum.REBALANCE,
                created_by=user_token,
                change_reason="Periodic rebalance"
            )

            portfolio.current_version_id = version.id
            portfolio.version_hash = version.state_hash

            self.db.commit()

            return await self._build_portfolio_response(portfolio, user_token)

        except (PortfolioValidationError, PortfolioNotFoundError) as e:
            self.db.rollback()
            self.logger.warning(f"Rebalance validation failed: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error rebalancing portfolio {portfolio_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error rebalancing portfolio {portfolio_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def get_portfolio_performance(self, portfolio_id: int) -> Optional[PortfolioPerformanceResponse]:
        """Get portfolio performance metrics"""
        try:
            portfolio = self.repository.get_by_id(portfolio_id)
            if not portfolio:
                return None

            return PortfolioPerformanceResponse(
                portfolio_id=portfolio.id,
                symbol=portfolio.symbol,
                inception_to_date_return=None,  # TODO: Implement performance calculations
                year_to_date_return=None,
                one_year_return=None,
                three_year_annualized=None,
                five_year_annualized=None,
                volatility=None,
                sharpe_ratio=None,
                max_drawdown=None,
                benchmark_symbol=portfolio.benchmark_symbol,
                benchmark_returns=None,
                last_updated=datetime.now(timezone.utc)
            )

        except Exception as e:
            self.logger.error(f"Error getting portfolio performance {portfolio_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    # Versioning Operations

    async def rollback_to_version(self, portfolio_id: int, target_version_id: int,
                                  rolled_back_by: str, change_reason: str = None) -> PortfolioResponse:
        """Rollback portfolio to a specific version using versioning manager"""
        try:
            portfolio = self.repository.get_by_id(portfolio_id)
            if not portfolio:
                raise PortfolioNotFoundError(f"Portfolio {portfolio_id} not found")

            rolled_back_portfolio: Portfolio = self.versioning_manager.rollback_to_version(
                portfolio=portfolio,
                target_version_id=target_version_id,
                rolled_back_by=rolled_back_by,
                change_reason=change_reason
            )

            self.db.commit()
            return await self._build_portfolio_response(rolled_back_portfolio, rolled_back_by)

        except PortfolioNotFoundError as e:
            self.db.rollback()
            self.logger.warning(f"Rollback validation failed: {str(e)}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error rolling back portfolio {portfolio_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error rolling back portfolio {portfolio_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def get_version_history(self, portfolio_id: int) -> List[PortfolioVersion]:
        """Retrieve complete version history for a portfolio"""
        try:
            return self.versioning_manager.get_version_history(portfolio_id)
        except Exception as e:
            self.logger.error(f"Error getting version history for portfolio {portfolio_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def compare_versions(self, portfolio_id: int, version1_id: int, version2_id: int) -> Dict[str, Any]:
        """Compare differences between two portfolio versions"""
        try:
            return self.versioning_manager.compare_versions(
                portfolio_id=portfolio_id,
                version1_id=version1_id,
                version2_id=version2_id
            )
        except ValueError as e:
            self.logger.warning(f"Version comparison validation failed: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            self.logger.error(f"Error comparing versions {version1_id} and {version2_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def get_latest_version(self, portfolio_id: int) -> Optional[PortfolioVersion]:
        """Get the latest version of a portfolio"""
        try:
            return self.versioning_manager.get_latest_version(portfolio_id)
        except Exception as e:
            self.logger.error(f"Error getting latest version for portfolio {portfolio_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def get_specific_version(self, portfolio_id: int, version_id: int) -> Optional[PortfolioVersion]:
        """Get a specific version of a portfolio"""
        try:
            version = self.versioning_manager.get_version(portfolio_id, version_id)
            if not version:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Version {version_id} not found for portfolio {portfolio_id}"
                )
            return version
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting version {version_id} for portfolio {portfolio_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    # Helper Methods

    async def _adjust_weights(self, portfolio_id: int) -> None:
        """Adjust weights proportionally after adding/removing constituents"""
        constituents = self.db.query(Constituent).filter(
            Constituent.portfolio_id == portfolio_id
        ).all()

        total_weight = sum(Decimal(str(c.weight)) for c in constituents)

        if total_weight > 0:
            scale_factor = Decimal("1") / total_weight
            for constituent in constituents:
                constituent.weight = Decimal(str(constituent.weight)) * scale_factor
                constituent.target_weight = constituent.weight

    @staticmethod
    async def _rebalance_constituents(constituents: List[Constituent],
                                      methodology: WeightingMethodologyEnum) -> None:
        """Apply rebalancing logic based on weighting methodology"""
        if methodology == WeightingMethodologyEnum.EQUALLY_WEIGHTED:
            total_constituents = len(constituents)
            if total_constituents > 0:
                equal_weight = Decimal("1") / Decimal(str(total_constituents))
                for constituent in constituents:
                    constituent.target_weight = equal_weight

        elif methodology == WeightingMethodologyEnum.MARKET_CAP_WEIGHTED:
            total_market_value = sum(
                c.market_value for c in constituents if c.market_value
            )
            if total_market_value and total_market_value > 0:
                for constituent in constituents:
                    if constituent.market_value:
                        constituent.target_weight = Decimal(str(constituent.market_value)) / Decimal(
                            str(total_market_value))


# Factory function for dependency injection
def create_portfolio_service(
        db: Session = Depends(get_db),
        equity_client: EquityServiceClient = Depends(get_equity_service),
        fixed_income_client: FixedIncomeServiceClient = Depends(get_fixed_income_service)
) -> PortfolioService:
    """Factory function to create PortfolioService with dependencies"""
    config = PortfolioServiceConfig()
    return PortfolioService(
        db=db,
        equity_client=equity_client,
        fixed_income_client=fixed_income_client,
        config=config
    )
