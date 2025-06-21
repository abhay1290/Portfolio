import logging
from typing import Any, Dict, List, Tuple

from fastapi import HTTPException, status

from fixed_income.src.database.bond_database_service import BondDatabaseService
from fixed_income.src.model.bonds.BondBase import BondBase
from fixed_income.src.model.enums import BondTypeEnum
from fixed_income.src.services.fixed_income_read_service import BondReadOnlyService, get_bond_read_service
from fixed_income.src.utils.model_mappers import bond_model_factory, bond_schema_factory

logger = logging.getLogger(__name__)


class BondWriteService:
    """
    Pure Write-Only Bond Service

    Handles all write operations (Create, Update, Delete) for different bond types.
    Depends on BondReadOnlyService for validation and reads.
    Includes cache invalidation hooks for future caching implementation.
    """

    def __init__(self):
        self._db_services = {}  # Cache for database services by bond type
        self.read_service: BondReadOnlyService = get_bond_read_service()

    def _get_db_service(self, bond_type: BondTypeEnum) -> BondDatabaseService:
        """Get or create database service for specific bond type"""
        if bond_type not in self._db_services:
            model_class = bond_model_factory(bond_type.value)
            schemas = bond_schema_factory(bond_type.value)

            self._db_services[bond_type] = BondDatabaseService(
                bond_base_model=BondBase,
                model=model_class,
                create_schema=schemas['request'],
                response_schema=schemas['response'],
                update_schema=schemas['request']
            )

        return self._db_services[bond_type]

    # === Core Write Operations ===

    async def create_bond(
            self,
            bond_data: Any,
            bond_type: BondTypeEnum,
            user_token: str = None
    ) -> Any:
        """
        Create a new bond instrument of a specific type.
        """
        try:
            # Validate symbol uniqueness if provided
            if hasattr(bond_data, 'symbol') and bond_data.symbol:
                if not await self.read_service.validate_symbol_unique(bond_data.symbol, bond_type):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"{bond_type.value} bond with symbol {bond_data.symbol} already exists"
                    )

            # Create bond
            db_service = self._get_db_service(bond_type)
            bond_response = await db_service.create(bond_data)

            # Future: Invalidate relevant caches
            # await self.read_service.invalidate_cache(bond_response.id, bond_type)
            # if hasattr(bond_response, 'symbol') and bond_response.symbol:
            #     await self.read_service.invalidate_symbol_cache(bond_response.symbol, bond_type)

            logger.info(f"Created {bond_type.value} bond with ID {bond_response.id}")
            return bond_response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating {bond_type.value} bond: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create {bond_type.value} bond instrument"
            )

    async def update_bond(
            self,
            bond_id: int,
            bond_data: Any,
            bond_type: BondTypeEnum,
            user_token: str = None
    ) -> Any:
        """
        Fully update an existing bond instrument of a specific type.
        """
        try:
            # Validate bond exists
            existing_bond = await self.read_service.get_bond_by_id(bond_id, bond_type)
            if not existing_bond:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{bond_type.value} bond with ID {bond_id} not found"
                )

            # Validate symbol uniqueness if changing
            if (hasattr(bond_data, 'symbol') and hasattr(existing_bond, 'symbol') and
                    bond_data.symbol != existing_bond.symbol):
                if not await self.read_service.validate_symbol_unique(bond_data.symbol, bond_type, exclude_id=bond_id):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"{bond_type.value} bond with symbol {bond_data.symbol} already exists"
                    )

            # Update bond
            db_service = self._get_db_service(bond_type)
            updated_bond = await db_service.update(bond_id, bond_data)

            # Future: Invalidate caches
            # await self.read_service.invalidate_cache(bond_id, bond_type)
            # if hasattr(existing_bond, 'symbol') and existing_bond.symbol:
            #     await self.read_service.invalidate_symbol_cache(existing_bond.symbol, bond_type)
            # if (hasattr(bond_data, 'symbol') and hasattr(existing_bond, 'symbol') and
            #     bond_data.symbol != existing_bond.symbol):
            #     await self.read_service.invalidate_symbol_cache(bond_data.symbol, bond_type)

            logger.info(f"Updated {bond_type.value} bond {bond_id}")
            return updated_bond

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating {bond_type.value} bond {bond_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update {bond_type.value} bond"
            )

    async def partial_update_bond(
            self,
            bond_id: int,
            bond_data: Any,
            bond_type: BondTypeEnum,
            user_token: str = None
    ) -> Any:
        """
        Partially update an existing bond instrument of a specific type.
        """
        try:
            # Validate bond exists
            existing_bond = await self.read_service.get_bond_by_id(bond_id, bond_type)
            if not existing_bond:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{bond_type.value} bond with ID {bond_id} not found"
                )

            # Validate symbol uniqueness if changing
            if (hasattr(bond_data, 'symbol') and bond_data.symbol and
                    hasattr(existing_bond, 'symbol') and bond_data.symbol != existing_bond.symbol):
                if not await self.read_service.validate_symbol_unique(bond_data.symbol, bond_type, exclude_id=bond_id):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"{bond_type.value} bond with symbol {bond_data.symbol} already exists"
                    )

            # Partial update
            db_service = self._get_db_service(bond_type)
            updated_bond = await db_service.partial_update(bond_id, bond_data)

            # Future: Invalidate caches
            # await self.read_service.invalidate_cache(bond_id, bond_type)
            # if hasattr(existing_bond, 'symbol') and existing_bond.symbol:
            #     await self.read_service.invalidate_symbol_cache(existing_bond.symbol, bond_type)

            logger.info(f"Partially updated {bond_type.value} bond {bond_id}")
            return updated_bond

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error partially updating {bond_type.value} bond {bond_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to partially update {bond_type.value} bond"
            )

    async def delete_bond(
            self,
            bond_id: int,
            bond_type: BondTypeEnum,
            user_token: str = None
    ) -> bool:
        """
        Delete a bond instrument of a specific type.
        """
        try:
            # Validate bond exists first
            existing_bond = await self.read_service.get_bond_by_id(bond_id, bond_type)
            if not existing_bond:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{bond_type.value} bond with ID {bond_id} not found"
                )

            # Delete bond
            db_service = self._get_db_service(bond_type)
            success = await db_service.delete(bond_id)

            if success:
                # Future: Invalidate caches
                # await self.read_service.invalidate_cache(bond_id, bond_type)
                # if hasattr(existing_bond, 'symbol') and existing_bond.symbol:
                #     await self.read_service.invalidate_symbol_cache(existing_bond.symbol, bond_type)

                logger.info(f"Deleted {bond_type.value} bond {bond_id}")

            return success

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting {bond_type.value} bond {bond_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete {bond_type.value} bond"
            )

    # === Bulk Write Operations ===

    async def bulk_create_bonds(
            self,
            bulk_request: List[Any],
            bond_type: BondTypeEnum,
            user_token: str = None
    ) -> List[Any]:
        """
        Create multiple bond instruments in bulk for a specific bond type.
        """
        try:
            # Pre-validate all symbols for uniqueness
            validated_requests = []
            skipped_symbols = []

            for bond_request in bulk_request:
                symbol = getattr(bond_request, 'symbol', None)
                if symbol and not await self.read_service.validate_symbol_unique(symbol, bond_type):
                    skipped_symbols.append(symbol)
                    logger.warning(f"Skipping duplicate symbol {symbol} in bulk create for {bond_type.value}")
                else:
                    validated_requests.append(bond_request)

            if not validated_requests:
                logger.warning(f"No valid {bond_type.value} bonds to create in bulk request")
                return []

            # Bulk create
            db_service = self._get_db_service(bond_type)
            results = await db_service.bulk_create(validated_requests)

            # Future: Invalidate relevant caches
            # for bond in results:
            #     await self.read_service.invalidate_cache(bond.id, bond_type)
            #     if hasattr(bond, 'symbol') and bond.symbol:
            #         await self.read_service.invalidate_symbol_cache(bond.symbol, bond_type)

            logger.info(
                f"Bulk created {len(results)} {bond_type.value} bonds, skipped {len(skipped_symbols)} duplicates")
            return results

        except Exception as e:
            logger.error(f"Error in bulk create {bond_type.value} bonds: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to bulk create {bond_type.value} bonds"
            )

    async def bulk_update_bonds(
            self,
            updates: List[Tuple[int, Any]],
            bond_type: BondTypeEnum,
            user_token: str = None
    ) -> List[Any]:
        """
        Update multiple bond instruments in bulk for a specific bond type.
        """
        results = []
        errors = []

        for bond_id, bond_request in updates:
            try:
                updated_bond = await self.update_bond(bond_id, bond_request, bond_type, user_token)
                results.append(updated_bond)
            except Exception as e:
                logger.error(f"Error updating {bond_type.value} bond {bond_id} in bulk: {str(e)}")
                errors.append({"bond_id": bond_id, "bond_type": bond_type.value, "error": str(e)})

        if errors:
            logger.warning(f"Bulk update completed with {len(errors)} errors for {bond_type.value}")

        return results

    async def bulk_delete_bonds(
            self,
            bond_ids: List[int],
            bond_type: BondTypeEnum,
            user_token: str = None
    ) -> Dict[int, bool]:
        """
        Delete multiple bond instruments in bulk for a specific bond type.
        """
        results = {}

        for bond_id in bond_ids:
            try:
                success = await self.delete_bond(bond_id, bond_type, user_token)
                results[bond_id] = success
            except Exception as e:
                logger.error(f"Error deleting {bond_type.value} bond {bond_id} in bulk: {str(e)}")
                results[bond_id] = False

        return results

    # === Price Update Operations ===

    async def update_bond_price(
            self,
            bond_id: int,
            new_price: float,
            bond_type: BondTypeEnum,
            user_token: str = None
    ) -> Any:
        """
        Update price for a single bond instrument of a specific type.
        """
        try:
            # Get current bond data
            existing_bond = await self.read_service.get_bond_by_id(bond_id, bond_type)
            if not existing_bond:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{bond_type.value} bond with ID {bond_id} not found"
                )

            # Create price update - need to get the appropriate request schema
            schemas = bond_schema_factory(bond_type.value)
            request_schema = schemas['request']

            # Create minimal update with just price change
            # This assumes the request schema has a current_price field
            update_data = {}
            for field_name, field_info in request_schema.__fields__.items():
                if field_name == 'current_price':
                    update_data[field_name] = new_price
                elif hasattr(existing_bond, field_name):
                    update_data[field_name] = getattr(existing_bond, field_name)

            price_update_data = request_schema(**update_data)

            # Update bond
            updated_bond = await self.partial_update_bond(bond_id, price_update_data, bond_type, user_token)

            logger.info(f"Updated price for {bond_type.value} bond {bond_id} to {new_price}")
            return updated_bond

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update price for {bond_type.value} bond {bond_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update price for {bond_type.value} bond {bond_id}"
            )

    async def bulk_update_bond_prices(
            self,
            price_updates: List[Tuple[int, float]],
            bond_type: BondTypeEnum,
            user_token: str = None
    ) -> List[Any]:
        """
        Update prices for multiple bond instruments in bulk for a specific bond type.
        """
        results = []

        for bond_id, new_price in price_updates:
            try:
                result = await self.update_bond_price(bond_id, new_price, bond_type, user_token)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to update price for {bond_type.value} bond {bond_id}: {str(e)}")

        logger.info(f"Updated prices for {len(results)} {bond_type.value} bonds")
        return results

    # === Status Management ===

    async def activate_bond(
            self,
            bond_id: int,
            bond_type: BondTypeEnum,
            user_token: str = None
    ) -> Any:
        """
        Activate a bond instrument of a specific type.
        """
        try:
            existing_bond = await self.read_service.get_bond_by_id(bond_id, bond_type)
            if not existing_bond:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{bond_type.value} bond with ID {bond_id} not found"
                )

            # Create update with is_active = True
            schemas = bond_schema_factory(bond_type.value)
            request_schema = schemas['request']

            update_data = {}
            for field_name, field_info in request_schema.__fields__.items():
                if field_name == 'is_active':
                    update_data[field_name] = True
                elif hasattr(existing_bond, field_name):
                    update_data[field_name] = getattr(existing_bond, field_name)

            activation_data = request_schema(**update_data)

            return await self.partial_update_bond(bond_id, activation_data, bond_type, user_token)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error activating {bond_type.value} bond {bond_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to activate {bond_type.value} bond"
            )

    async def deactivate_bond(
            self,
            bond_id: int,
            bond_type: BondTypeEnum,
            user_token: str = None
    ) -> Any:
        """
        Deactivate a bond instrument of a specific type.
        """
        try:
            existing_bond = await self.read_service.get_bond_by_id(bond_id, bond_type)
            if not existing_bond:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{bond_type.value} bond with ID {bond_id} not found"
                )

            # Create update with is_active = False
            schemas = bond_schema_factory(bond_type.value)
            request_schema = schemas['request']

            update_data = {}
            for field_name, field_info in request_schema.__fields__.items():
                if field_name == 'is_active':
                    update_data[field_name] = False
                elif hasattr(existing_bond, field_name):
                    update_data[field_name] = getattr(existing_bond, field_name)

            deactivation_data = request_schema(**update_data)

            return await self.partial_update_bond(bond_id, deactivation_data, bond_type, user_token)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deactivating {bond_type.value} bond {bond_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to deactivate {bond_type.value} bond"
            )

    # === Multi-Type Operations ===

    async def bulk_create_mixed_bonds(
            self,
            bond_requests: List[Tuple[BondTypeEnum, Any]],  # List of (bond_type, bond_data) tuples
            user_token: str = None
    ) -> Dict[str, List[Any]]:
        """
        Create multiple bonds of different types in bulk.
        """
        results = {}

        # Group requests by bond type
        grouped_requests = {}
        for bond_type, bond_data in bond_requests:
            if bond_type not in grouped_requests:
                grouped_requests[bond_type] = []
            grouped_requests[bond_type].append(bond_data)

        # Process each bond type separately
        for bond_type, requests in grouped_requests.items():
            try:
                type_results = await self.bulk_create_bonds(requests, bond_type, user_token)
                results[bond_type.value] = type_results
            except Exception as e:
                logger.error(f"Error in mixed bulk create for {bond_type.value}: {str(e)}")
                results[bond_type.value] = []

        return results

    async def get_supported_bond_types(self) -> List[BondTypeEnum]:
        """
        Get list of supported bond types.
        """
        return list(BondTypeEnum)


# Factory function
def get_bond_write_service() -> BondWriteService:
    """Factory function for dependency injection"""
    return BondWriteService()
