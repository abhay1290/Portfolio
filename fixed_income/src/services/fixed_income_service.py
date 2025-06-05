import logging
from typing import List

from fastapi import Depends, HTTPException, status

from fixed_income.src.api.bond_schema.BondBaseSchema import BondBaseRequest, BondBaseResponse
from fixed_income.src.api.dependencies import PortfolioServiceClient, db_dependency, get_current_user, \
    portfolio_service_dependency
from fixed_income.src.api.routers.bond_crud_router import BondGenericRouter
from fixed_income.src.model.bonds import BondBase
from fixed_income.src.model.bonds.BondModelFactory import bond_model_factory

logger = logging.getLogger(__name__)


class FixedIncomeService:
    # TODO - check how to fix?
    def __init__(self):
        self.router = BondGenericRouter(
            bond_base_model=BondBase,
            model=bond_model_factory(BondBaseRequest.bond_type),
            create_schema=BondBaseRequest,
            response_schema=BondBaseResponse,
            base_path="/bonds",
            tags=["bonds"]
        )

    async def create_fixed_income_instrument(
            self,
            fixed_income_data: BondBaseRequest,
            db: db_dependency,
            current_user: dict = Depends(get_current_user),
            portfolio_service: PortfolioServiceClient = portfolio_service_dependency
    ) -> BondBaseResponse:
        """
        Create a new fixed_income with portfolio validation
        """
        # Validate portfolio exists
        await portfolio_service.get_portfolio(fixed_income_data.portfolio_id, current_user.get("access_token"))

        try:
            # Create the fixed_income using the generic router's method
            return await self.router.create_item(db, fixed_income_data)
        except HTTPException as e:
            logger.error(f"Error creating fixed_income: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error creating fixed_income: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create fixed_income"
            )

    async def get_fixed_income_instruments(
            self,
            db: db_dependency,
            skip: int = 0,
            limit: int = 100,
            current_user: dict = Depends(get_current_user)
    ) -> List[BondBaseResponse]:
        """
        Get list of fixed_income instruments with pagination
        """
        return await self.router.read_items(db, skip, limit)

    async def get_fixed_income_instrument(
            self,
            fixed_income_id: str,
            db: db_dependency,
            current_user: dict = Depends(get_current_user)
    ) -> BondBaseResponse:
        """
        Get a single fixed_income instrument by fixed_income_id
        """
        return await self.router.read_item(fixed_income_id, db)

    async def update_fixed_income_instrument(
            self,
            fixed_income_id: str,
            fixed_income_data: BondBaseRequest,
            db: db_dependency,
            current_user: dict = Depends(get_current_user),
            portfolio_service: PortfolioServiceClient = portfolio_service_dependency
    ) -> BondBaseResponse:
        """
        Update an existing fixed_income instrument
        """
        # If portfolio_id is being updated, validate the new portfolio exists
        if fixed_income_data.portfolio_id:
            await portfolio_service.get_portfolio(fixed_income_data.portfolio_id, current_user.get("access_token"))

        return await self.router.update_item(fixed_income_id, fixed_income_data, db)

    async def get_fixed_income_instrument_by_portfolio_id(
            self,
            portfolio_id: str,
            db: db_dependency,
            current_user: dict = Depends(get_current_user),
            portfolio_service: PortfolioServiceClient = portfolio_service_dependency,
            skip: int = 0,
            limit: int = 100
    ) -> List[BondBaseResponse]:
        """
        Get all fixed income instruments for a specific portfolio
        """
        # First validate the portfolio exists and user has access
        await portfolio_service.get_portfolio(portfolio_id, current_user.get("access_token"))

        # Then fetch the equities
        return await self.router.read_by_column("portfolio_id", portfolio_id, db, skip, limit)


def get_fixed_income_service() -> FixedIncomeService:
    return FixedIncomeService()
