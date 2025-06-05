import logging
from typing import List

from fastapi import Depends, HTTPException, status

from equity.src.api.dependencies import PortfolioServiceClient, db_dependency, get_current_user, \
    portfolio_service_dependency
from equity.src.api.equity_schema.Equity_Schema import EquityRequest, EquityResponse
from equity.src.api.routers.equity_crud_router import EquityGenericRouter
from equity.src.model.equity.Equity import Equity

logger = logging.getLogger(__name__)


class EquityService:
    def __init__(self):
        self.router = EquityGenericRouter(
            model=Equity,
            create_schema=EquityRequest,
            response_schema=EquityResponse,
            base_path="/equities",
            tags=["equities"]
        )

    async def create_equity(
            self,
            equity_data: EquityRequest,
            db: db_dependency,
            current_user: dict = Depends(get_current_user),
            portfolio_service: PortfolioServiceClient = portfolio_service_dependency
    ) -> EquityResponse:
        """
        Create a new equity with portfolio validation
        """
        # Validate portfolio exists
        await portfolio_service.get_portfolio(equity_data.portfolio_id, current_user.get("access_token"))

        try:
            # Create the equity using the generic router's method
            return await self.router.create_item(db, equity_data)
        except HTTPException as e:
            logger.error(f"Error creating equity: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error creating equity: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create equity"
            )

    async def get_equities(
            self,
            db: db_dependency,
            skip: int = 0,
            limit: int = 100,
            current_user: dict = Depends(get_current_user)
    ) -> List[EquityResponse]:
        """
        Get list of equities with pagination
        """
        return await self.router.read_items(db, skip, limit)

    async def get_equity(
            self,
            equity_id: str,
            db: db_dependency,
            current_user: dict = Depends(get_current_user)
    ) -> EquityResponse:
        """
        Get a single equity by ID
        """
        return await self.router.read_item(equity_id, db)

    async def update_equity(
            self,
            equity_id: str,
            equity_data: EquityRequest,
            db: db_dependency,
            current_user: dict = Depends(get_current_user),
            portfolio_service: PortfolioServiceClient = portfolio_service_dependency
    ) -> EquityResponse:
        """
        Update an existing equity
        """
        # If portfolio_id is being updated, validate the new portfolio exists
        if equity_data.portfolio_id:
            await portfolio_service.get_portfolio(equity_data.portfolio_id, current_user.get("access_token"))

        return await self.router.update_item(equity_id, equity_data, db)

    # async def partial_update_equity(
    #         self,
    #         equity_id: str,
    #         equity_data: EquityRequest,
    #         db: db_dependency,
    #         current_user: dict = Depends(get_current_user),
    #         portfolio_service: PortfolioServiceClient = portfolio_service_dependency
    # ) -> EquityResponse:
    #     """
    #     Partially update an existing equity
    #     """
    #     # If portfolio_id is being updated, validate the new portfolio exists
    #     if equity_data.portfolio_id:
    #         await portfolio_service.get_portfolio(equity_data.portfolio_id, current_user.get("access_token"))
    #
    #     return await self.router.partial_update_item(equity_id, equity_data, db)

    async def get_equities_by_portfolio(
            self,
            portfolio_id: str,
            db: db_dependency,
            current_user: dict = Depends(get_current_user),
            portfolio_service: PortfolioServiceClient = portfolio_service_dependency,
            skip: int = 0,
            limit: int = 100
    ) -> List[EquityResponse]:
        """
        Get all equities for a specific portfolio
        """
        # First validate the portfolio exists and user has access
        await portfolio_service.get_portfolio(portfolio_id, current_user.get("access_token"))

        # Then fetch the equities
        return await self.router.read_by_column("portfolio_id", portfolio_id, db, skip, limit)


def get_equity_service() -> EquityService:
    return EquityService()
