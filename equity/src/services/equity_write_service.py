import logging
from typing import Dict, List

from fastapi import HTTPException, status

from equity.src.api.equity_schema.Equity_Schema import (
    EquityRequest,
    EquityResponse
)
from equity.src.database.equity_database_service import EquityDatabaseService
from equity.src.model.equity.Equity import Equity
from equity.src.services.equity_read_service import get_equity_read_service

logger = logging.getLogger(__name__)


class EquityWriteService:
    """
    Pure Write-Only Equity Service

    Handles all write operations (Create, Update, Delete).
    Depends on EquityReadOnlyService for validation and reads.
    Includes cache invalidation hooks for future caching implementation.
    """

    def __init__(self):
        self.db_service = EquityDatabaseService(
            model=Equity,
            create_schema=EquityRequest,
            response_schema=EquityResponse,
            update_schema=EquityRequest
        )
        self.read_service = get_equity_read_service()

    # === Core Write Operations ===

    async def create_equity(
            self,
            equity_data: EquityRequest,
            user_token: str = None
    ) -> EquityResponse:
        """
        Create a new equity instrument.
        """
        try:
            # Validate symbol uniqueness
            if not await self.read_service.validate_symbol_unique(equity_data.symbol):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Equity with symbol {equity_data.symbol} already exists"
                )

            # Create equity
            equity_response = await self.db_service.create(equity_data)

            # Future: Invalidate relevant caches
            # await self.read_service.invalidate_cache(equity_response.id)
            # await self.read_service.invalidate_symbol_cache(equity_response.symbol)

            logger.info(f"Created equity {equity_response.symbol} with ID {equity_response.id}")
            return equity_response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating equity: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create equity instrument"
            )

    async def update_equity(
            self,
            equity_id: int,
            equity_data: EquityRequest,
            user_token: str = None
    ) -> EquityResponse:
        """
        Fully update an existing equity instrument.
        """
        try:
            # Validate equity exists
            existing_equity = await self.read_service.get_equity_by_id(equity_id)
            if not existing_equity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Equity with ID {equity_id} not found"
                )

            # Validate symbol uniqueness if changing
            if equity_data.symbol != existing_equity.symbol:
                if not await self.read_service.validate_symbol_unique(equity_data.symbol, exclude_id=equity_id):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Equity with symbol {equity_data.symbol} already exists"
                    )

            # Update equity
            updated_equity = await self.db_service.update(equity_id, equity_data)

            # Future: Invalidate caches
            # await self.read_service.invalidate_cache(equity_id)
            # await self.read_service.invalidate_symbol_cache(existing_equity.symbol)
            # if equity_data.symbol != existing_equity.symbol:
            #     await self.read_service.invalidate_symbol_cache(equity_data.symbol)

            logger.info(f"Updated equity {equity_id}")
            return updated_equity

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating equity {equity_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update equity"
            )

    async def partial_update_equity(
            self,
            equity_id: int,
            equity_data: EquityRequest,
            user_token: str = None
    ) -> EquityResponse:
        """
        Partially update an existing equity instrument.
        """
        try:
            # Validate equity exists
            existing_equity = await self.read_service.get_equity_by_id(equity_id)
            if not existing_equity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Equity with ID {equity_id} not found"
                )

            # Validate symbol uniqueness if changing
            if equity_data.symbol and equity_data.symbol != existing_equity.symbol:
                if not await self.read_service.validate_symbol_unique(equity_data.symbol, exclude_id=equity_id):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Equity with symbol {equity_data.symbol} already exists"
                    )

            # Partial update
            updated_equity = await self.db_service.partial_update(equity_id, equity_data)

            # Future: Invalidate caches
            # await self.read_service.invalidate_cache(equity_id)
            # await self.read_service.invalidate_symbol_cache(existing_equity.symbol)

            logger.info(f"Partially updated equity {equity_id}")
            return updated_equity

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error partially updating equity {equity_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to partially update equity"
            )

    async def delete_equity(
            self,
            equity_id: int,
            user_token: str = None
    ) -> bool:
        """
        Delete an equity instrument.
        """
        try:
            # Validate equity exists first
            existing_equity = await self.read_service.get_equity_by_id(equity_id)
            if not existing_equity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Equity with ID {equity_id} not found"
                )

            # Delete equity
            success = await self.db_service.delete(equity_id)

            if success:
                # Future: Invalidate caches
                # await self.read_service.invalidate_cache(equity_id)
                # await self.read_service.invalidate_symbol_cache(existing_equity.symbol)

                logger.info(f"Deleted equity {equity_id}")

            return success

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting equity {equity_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete equity"
            )

    # === Bulk Write Operations ===

    async def bulk_create_equities(
            self,
            bulk_request: List[EquityRequest],
            user_token: str = None
    ) -> List[EquityResponse]:
        """
        Create multiple equity instruments in bulk.
        """
        try:
            # Pre-validate all symbols for uniqueness
            validated_requests = []
            skipped_symbols = []

            for equity_request in bulk_request:
                if await self.read_service.validate_symbol_unique(equity_request.symbol):
                    validated_requests.append(equity_request)
                else:
                    skipped_symbols.append(equity_request.symbol)
                    logger.warning(f"Skipping duplicate symbol {equity_request.symbol} in bulk create")

            if not validated_requests:
                logger.warning("No valid equities to create in bulk request")
                return []

            # Bulk create
            results = await self.db_service.bulk_create(validated_requests)

            # Future: Invalidate relevant caches
            # for equity in results:
            #     await self.read_service.invalidate_cache(equity.id)
            #     await self.read_service.invalidate_symbol_cache(equity.symbol)

            logger.info(f"Bulk created {len(results)} equities, skipped {len(skipped_symbols)} duplicates")
            return results

        except Exception as e:
            logger.error(f"Error in bulk create equities: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to bulk create equities"
            )

    async def bulk_update_equities(
            self,
            updates: List[tuple[int, EquityRequest]],
            user_token: str = None
    ) -> List[EquityResponse]:
        """
        Update multiple equity instruments in bulk.
        """
        results = []
        errors = []

        for equity_id, equity_request in updates:
            try:
                updated_equity = await self.update_equity(equity_id, equity_request, user_token)
                results.append(updated_equity)
            except Exception as e:
                logger.error(f"Error updating equity {equity_id} in bulk: {str(e)}")
                errors.append({"equity_id": equity_id, "error": str(e)})

        if errors:
            logger.warning(f"Bulk update completed with {len(errors)} errors")

        return results

    async def bulk_delete_equities(
            self,
            equity_ids: List[int],
            user_token: str = None
    ) -> Dict[int, bool]:
        """
        Delete multiple equity instruments in bulk.
        """
        results = {}

        for equity_id in equity_ids:
            try:
                success = await self.delete_equity(equity_id, user_token)
                results[equity_id] = success
            except Exception as e:
                logger.error(f"Error deleting equity {equity_id} in bulk: {str(e)}")
                results[equity_id] = False

        return results

    # # === Price Update Operations ===
    #
    # async def update_equity_price(
    #         self,
    #         equity_id: int,
    #         new_price: float,
    #         user_token: str = None
    # ) -> EquityPriceResponse:
    #     """
    #     Update price for a single equity instrument.
    #     """
    #     try:
    #         # Get current equity data
    #         existing_equity = await self.read_service.get_equity_by_id(equity_id)
    #         if not existing_equity:
    #             raise HTTPException(
    #                 status_code=status.HTTP_404_NOT_FOUND,
    #                 detail=f"Equity with ID {equity_id} not found"
    #             )
    #
    #         old_price = existing_equity.current_price
    #
    #         # Create minimal update with just price change
    #         price_update_data = EquityRequest(
    #             symbol=existing_equity.symbol,
    #             company_name=existing_equity.company_name,
    #             current_price=new_price,
    #             sector=existing_equity.sector,
    #             currency=existing_equity.currency,
    #             is_active=existing_equity.is_active
    #         )
    #
    #         # Update equity
    #         await self.partial_update_equity(equity_id, price_update_data, user_token)
    #
    #         return EquityPriceResponse(
    #             equity_id=equity_id,
    #             symbol=existing_equity.symbol,
    #             old_price=old_price,
    #             new_price=new_price,
    #             updated_at=datetime.now()
    #         )
    #
    #     except HTTPException:
    #         raise
    #     except Exception as e:
    #         logger.error(f"Failed to update price for equity {equity_id}: {str(e)}")
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail=f"Failed to update price for equity {equity_id}"
    #         )
    #
    # async def bulk_update_equity_prices(
    #         self,
    #         price_updates: List[EquityPriceRequest],
    #         user_token: str = None
    # ) -> List[EquityPriceResponse]:
    #     """
    #     Update prices for multiple equity instruments in bulk.
    #     """
    #     results = []
    #
    #     for price_update in price_updates:
    #         try:
    #             result = await self.update_equity_price(
    #                 price_update.equity_id,
    #                 price_update.price,
    #                 user_token
    #             )
    #             results.append(result)
    #         except Exception as e:
    #             logger.error(f"Failed to update price for equity {price_update.equity_id}: {str(e)}")
    #
    #     logger.info(f"Updated prices for {len(results)} equities")
    #     return results

    # === Status Management ===

    async def activate_equity(
            self,
            equity_id: int,
            user_token: str = None
    ) -> EquityResponse:
        """
        Activate an equity instrument.
        """
        try:
            existing_equity = await self.read_service.get_equity_by_id(equity_id)
            if not existing_equity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Equity with ID {equity_id} not found"
                )

            # Create update with is_active = True
            update_data = EquityRequest(
                symbol=existing_equity.symbol,
                company_name=existing_equity.company_name,
                current_price=existing_equity.current_price,
                sector=existing_equity.sector,
                currency=existing_equity.currency,
                is_active=True
            )

            return await self.partial_update_equity(equity_id, update_data, user_token)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error activating equity {equity_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate equity"
            )

    async def deactivate_equity(
            self,
            equity_id: int,
            user_token: str = None
    ) -> EquityResponse:
        """
        Deactivate an equity instrument.
        """
        try:
            existing_equity = await self.read_service.get_equity_by_id(equity_id)
            if not existing_equity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Equity with ID {equity_id} not found"
                )

            # Create update with is_active = False
            update_data = EquityRequest(
                symbol=existing_equity.symbol,
                company_name=existing_equity.company_name,
                current_price=existing_equity.current_price,
                sector=existing_equity.sector,
                currency=existing_equity.currency,
                is_active=False
            )

            return await self.partial_update_equity(equity_id, update_data, user_token)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deactivating equity {equity_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate equity"
            )


# Factory function
def get_equity_write_service() -> EquityWriteService:
    """Factory function for dependency injection"""
    return EquityWriteService()
