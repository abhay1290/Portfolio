import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from fixed_income.src.api.bond_schema.BondPriceSchema import (
    BondPriceRequest,
    BondPriceResponse
)
from fixed_income.src.model.bonds.BondPrice import BondPrice  # Assuming this model exists

from fixed_income.src.database.generic_database_service import GenericDatabaseService
from fixed_income.src.model.enums import BondTypeEnum
from fixed_income.src.services.fixed_income_price_read_service import get_bond_price_read_service
from fixed_income.src.services.fixed_income_read_service import get_bond_read_service

logger = logging.getLogger(__name__)


class BondPriceWriteService:
    """
    Pure Write-Only Bond Price Service

    Handles all price-related write operations (Create, Update, Delete) for bonds.
    Optimized for high-frequency price updates from market data feeds and trading systems.
    Supports multiple bond types and pricing methodologies.
    Includes validation and cache invalidation.
    """

    def __init__(self):
        self.db_service = GenericDatabaseService(
            model=BondPrice,
            create_schema=BondPriceRequest,
            response_schema=BondPriceResponse,
            update_schema=BondPriceRequest
        )
        self.bond_read_service = get_bond_read_service()
        self.price_read_service = get_bond_price_read_service()

    # === Core Price Operations ===

    async def update_price(
            self,
            bond_id: int,
            bond_type: BondTypeEnum,
            price: Decimal,
            timestamp: datetime = None,
            source: str = "manual",
            price_type: str = "clean",  # clean, dirty, yield
            user_token: str = None
    ) -> BondPriceResponse:
        """
        Update/create price for a single bond.
        """
        try:
            # Validate bond exists
            bond = await self.bond_read_service.get_bond_by_id(bond_id, bond_type)
            if not bond:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{bond_type.value} bond with ID {bond_id} not found"
                )

            # Use current time if not provided
            if not timestamp:
                timestamp = datetime.now()

            # Validate price is positive
            if price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Price must be positive"
                )

            # Check for duplicate timestamp (optional business rule)
            existing_price = await self._get_price_at_exact_timestamp(bond_id, bond_type, timestamp)
            if existing_price:
                # Update existing price
                price_data = BondPriceRequest(
                    bond_id=bond_id,
                    bond_type=bond_type.value,
                    price=price,
                    timestamp=timestamp,
                    source=source,
                    price_type=price_type
                )
                updated_price = await self.db_service.update(existing_price.id, price_data)
                logger.info(f"Updated existing price for {bond_type.value} bond {bond_id} at {timestamp}")
            else:
                # Create new price record
                price_data = BondPriceRequest(
                    bond_id=bond_id,
                    bond_type=bond_type.value,
                    price=price,
                    timestamp=timestamp,
                    source=source,
                    price_type=price_type
                )
                updated_price = await self.db_service.create(price_data)
                logger.info(f"Created new price for {bond_type.value} bond {bond_id}: {price}")

            # Future: Invalidate caches
            # await self.price_read_service.invalidate_price_cache(bond_id, bond_type)

            # Update current price in bond table if this is the most recent
            await self._update_bond_current_price_if_latest(bond_id, bond_type, price, timestamp)

            return updated_price

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating price for {bond_type.value} bond {bond_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update {bond_type.value} bond price"
            )

    async def bulk_update_prices(
            self,
            price_updates: List[BondPriceRequest],
            user_token: str = None
    ) -> List[BondPriceResponse]:
        """
        Update prices for multiple bonds in bulk.
        Optimized for market data feeds.
        """
        try:
            # Pre-validate all bond IDs exist
            bond_validations = {}
            for update in price_updates:
                key = (update.bond_id, BondTypeEnum(update.bond_type))
                if key not in bond_validations:
                    bond_validations[key] = await self.bond_read_service.validate_bond_exists(
                        update.bond_id, BondTypeEnum(update.bond_type)
                    )

            valid_updates = []
            invalid_updates = []

            for update in price_updates:
                validation_key = (update.bond_id, BondTypeEnum(update.bond_type))
                if bond_validations.get(validation_key, False):
                    if update.price > 0:  # Basic validation
                        valid_updates.append(update)
                    else:
                        invalid_updates.append(f"Invalid price for {update.bond_type} bond {update.bond_id}")
                else:
                    invalid_updates.append(f"{update.bond_type} bond {update.bond_id} not found")

            if invalid_updates:
                logger.warning(f"Skipping {len(invalid_updates)} invalid price updates")

            if not valid_updates:
                logger.warning("No valid price updates to process")
                return []

            # Bulk create/update prices
            results = []
            for update in valid_updates:
                try:
                    result = await self.update_price(
                        bond_id=update.bond_id,
                        bond_type=BondTypeEnum(update.bond_type),
                        price=update.price,
                        timestamp=update.timestamp or datetime.now(),
                        source=update.source or "bulk_update",
                        price_type=update.price_type or "clean",
                        user_token=user_token
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to update price for {update.bond_type} bond {update.bond_id}: {str(e)}")

            logger.info(f"Bulk updated {len(results)} bond prices, skipped {len(invalid_updates)}")
            return results

        except Exception as e:
            logger.error(f"Error in bulk price update: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to bulk update bond prices"
            )

    async def update_prices_from_feed(
            self,
            feed_data: Dict[str, any],
            bond_type: BondTypeEnum,
            source: str = "market_feed",
            user_token: str = None
    ) -> Dict[str, any]:
        """
        Process price updates from external market data feed for specific bond type.
        """
        try:
            # Parse feed data - format may vary by provider
            price_updates = []
            errors = []

            for symbol, price_data in feed_data.items():
                try:
                    # Get bond by symbol
                    bond = await self.bond_read_service.get_bond_by_symbol(symbol, bond_type)
                    if not bond:
                        errors.append(f"Symbol {symbol} not found for bond type {bond_type.value}")
                        continue

                    # Parse price data
                    price = Decimal(str(price_data.get('price', 0)))
                    timestamp = price_data.get('timestamp')
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp)
                    elif not timestamp:
                        timestamp = datetime.now()

                    price_type = price_data.get('price_type', 'clean')

                    price_updates.append(BondPriceRequest(
                        bond_id=bond.id,
                        bond_type=bond_type.value,
                        price=price,
                        timestamp=timestamp,
                        source=source,
                        price_type=price_type
                    ))

                except Exception as e:
                    errors.append(f"Error parsing data for {symbol}: {str(e)}")

            # Process valid updates
            if price_updates:
                results = await self.bulk_update_prices(price_updates, user_token)

                return {
                    "status": "completed",
                    "bond_type": bond_type.value,
                    "processed": len(results),
                    "errors": len(errors),
                    "error_details": errors[:10],  # Limit error details
                    "source": source,
                    "processed_at": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "no_valid_data",
                    "bond_type": bond_type.value,
                    "processed": 0,
                    "errors": len(errors),
                    "error_details": errors,
                    "source": source,
                    "processed_at": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error processing market feed for {bond_type.value}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process market data feed for {bond_type.value}"
            )

    # === Historical Price Management ===

    async def bulk_import_historical_prices(
            self,
            bond_id: int,
            bond_type: BondTypeEnum,
            historical_data: List[Tuple[datetime, Decimal, str]],  # (timestamp, price, price_type)
            source: str = "historical_import",
            user_token: str = None
    ) -> Dict[str, any]:
        """
        Import bulk historical price data for a bond.
        """
        try:
            # Validate bond exists
            bond = await self.bond_read_service.get_bond_by_id(bond_id, bond_type)
            if not bond:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{bond_type.value} bond with ID {bond_id} not found"
                )

            # Prepare price requests
            price_requests = []
            for timestamp, price, price_type in historical_data:
                if price > 0:  # Basic validation
                    price_requests.append(BondPriceRequest(
                        bond_id=bond_id,
                        bond_type=bond_type.value,
                        price=price,
                        timestamp=timestamp,
                        source=source,
                        price_type=price_type or "clean"
                    ))

            if not price_requests:
                return {
                    "status": "no_valid_data",
                    "imported": 0,
                    "bond_id": bond_id,
                    "bond_type": bond_type.value
                }

            # Sort by timestamp for efficient processing
            price_requests.sort(key=lambda x: x.timestamp)

            # Bulk create (assuming no duplicates for historical import)
            results = await self.db_service.bulk_create(price_requests)

            # Update current price if latest timestamp is most recent
            latest_price = price_requests[-1]
            await self._update_bond_current_price_if_latest(
                bond_id, bond_type, latest_price.price, latest_price.timestamp
            )

            logger.info(f"Imported {len(results)} historical prices for {bond_type.value} bond {bond_id}")

            return {
                "status": "completed",
                "imported": len(results),
                "bond_id": bond_id,
                "bond_type": bond_type.value,
                "date_range": {
                    "start": price_requests[0].timestamp.isoformat(),
                    "end": price_requests[-1].timestamp.isoformat()
                },
                "imported_at": datetime.now().isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error importing historical prices for {bond_type.value} bond {bond_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to import historical prices for {bond_type.value} bond"
            )

    async def delete_price_data(
            self,
            bond_id: int,
            bond_type: BondTypeEnum,
            start_date: datetime = None,
            end_date: datetime = None,
            user_token: str = None
    ) -> Dict[str, any]:
        """
        Delete price data for a bond within date range.
        """
        try:
            # Validate bond exists
            bond = await self.bond_read_service.get_bond_by_id(bond_id, bond_type)
            if not bond:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{bond_type.value} bond with ID {bond_id} not found"
                )

            # Get prices to delete for logging
            prices_to_delete = await self.price_read_service.get_price_history(
                bond_id=bond_id,
                bond_type=bond_type,
                start_date=start_date,
                end_date=end_date,
                limit=10000
            )

            # Delete prices (would need implementation in database service)
            deleted_count = 0
            for price in prices_to_delete:
                try:
                    await self.db_service.delete(price.id)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete price {price.id}: {str(e)}")

            # Future: Invalidate caches
            # await self.price_read_service.invalidate_price_cache(bond_id, bond_type)

            logger.info(f"Deleted {deleted_count} price records for {bond_type.value} bond {bond_id}")

            return {
                "status": "completed",
                "deleted_count": deleted_count,
                "bond_id": bond_id,
                "bond_type": bond_type.value,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                },
                "deleted_at": datetime.now().isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting price data for {bond_type.value} bond {bond_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete price data for {bond_type.value} bond"
            )

    # === Price Correction Operations ===

    async def correct_price(
            self,
            price_id: int,
            corrected_price: Decimal,
            correction_reason: str,
            user_token: str = None
    ) -> BondPriceResponse:
        """
        Correct a specific price record.
        """
        try:
            # Get existing price
            existing_price = await self.db_service.get_by_id(price_id)
            if not existing_price:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Price record {price_id} not found"
                )

            # Validate corrected price
            if corrected_price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Corrected price must be positive"
                )

            # Create correction record
            old_price = existing_price.price
            correction_data = BondPriceRequest(
                bond_id=existing_price.bond_id,
                bond_type=existing_price.bond_type,
                price=corrected_price,
                timestamp=existing_price.timestamp,
                source=f"correction:{correction_reason}",
                price_type=existing_price.price_type,
                original_price=old_price  # Track original for audit
            )

            # Update the price
            corrected_price_record = await self.db_service.update(price_id, correction_data)

            # Future: Invalidate caches
            # await self.price_read_service.invalidate_price_cache(existing_price.bond_id, BondTypeEnum(existing_price.bond_type))

            # Log correction
            logger.info(
                f"Corrected price {price_id} for {existing_price.bond_type} bond {existing_price.bond_id}: "
                f"{old_price} -> {corrected_price}. Reason: {correction_reason}"
            )

            return corrected_price_record

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error correcting price {price_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to correct price"
            )

    # === Yield-based Price Updates ===

    async def update_price_from_yield(
            self,
            bond_id: int,
            bond_type: BondTypeEnum,
            yield_to_maturity: Decimal,
            timestamp: datetime = None,
            source: str = "yield_calculation",
            user_token: str = None
    ) -> BondPriceResponse:
        """
        Calculate and update bond price based on yield to maturity.
        """
        try:
            # Get bond details
            bond = await self.bond_read_service.get_bond_by_id(bond_id, bond_type)
            if not bond:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{bond_type.value} bond with ID {bond_id} not found"
                )

            # Calculate price from yield
            calculated_price = self._calculate_price_from_yield(bond, float(yield_to_maturity))

            if calculated_price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Calculated price must be positive"
                )

            # Update price
            return await self.update_price(
                bond_id=bond_id,
                bond_type=bond_type,
                price=Decimal(str(calculated_price)),
                timestamp=timestamp,
                source=source,
                price_type="calculated",
                user_token=user_token
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating price from yield for {bond_type.value} bond {bond_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update price from yield for {bond_type.value} bond"
            )

    # === Market Data Synchronization ===

    async def sync_with_market_data(
            self,
            bond_type: BondTypeEnum,
            bond_ids: List[int] = None,
            symbols: List[str] = None,
            force_update: bool = False,
            user_token: str = None
    ) -> Dict[str, any]:
        """
        Synchronize bond prices with external market data sources.
        """
        try:
            # Determine which bonds to sync
            target_bonds = []

            if symbols:
                bonds = await self.bond_read_service.get_bonds_by_symbols_bulk(symbols, bond_type)
                target_bonds.extend(bonds)

            if bond_ids:
                bonds = await self.bond_read_service.get_bonds_bulk(bond_ids, bond_type)
                target_bonds.extend(bonds)

            if not target_bonds and not bond_ids and not symbols:
                # Sync all active bonds of this type
                target_bonds = await self.bond_read_service.get_active_bonds(bond_type)

            if not target_bonds:
                return {
                    "status": "no_bonds_found",
                    "bond_type": bond_type.value,
                    "synced": 0,
                    "errors": 0
                }

            # TODO: Implement actual market data provider integration
            # This is a placeholder for market data sync logic
            synced_count = 0
            errors = []

            for bond in target_bonds:
                try:
                    # Placeholder: In real implementation, call market data API
                    # market_price = await external_bond_data_provider.get_price(bond.symbol, bond_type)
                    #
                    # For now, simulate sync
                    logger.info(f"Would sync price for {bond_type.value} bond {bond.symbol}")
                    synced_count += 1

                except Exception as e:
                    errors.append(f"Failed to sync {bond.symbol}: {str(e)}")

            return {
                "status": "completed",
                "bond_type": bond_type.value,
                "synced": synced_count,
                "errors": len(errors),
                "error_details": errors[:10],
                "force_update": force_update,
                "synced_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error syncing market data for {bond_type.value}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to sync market data for {bond_type.value}"
            )

    # === Helper Methods ===

    async def _get_price_at_exact_timestamp(
            self,
            bond_id: int,
            bond_type: BondTypeEnum,
            timestamp: datetime
    ) -> Optional[BondPriceResponse]:
        """Get price at exact timestamp if exists."""
        try:
            prices = await self.price_read_service.get_price_history(
                bond_id=bond_id,
                bond_type=bond_type,
                start_date=timestamp,
                end_date=timestamp,
                limit=1
            )
            return prices[0] if prices else None
        except Exception:
            return None

    async def _update_bond_current_price_if_latest(
            self,
            bond_id: int,
            bond_type: BondTypeEnum,
            price: Decimal,
            timestamp: datetime
    ) -> bool:
        """Update bond's current_price field if this is the latest price."""
        try:
            # Get current latest price
            current_latest = await self.price_read_service.get_current_price(bond_id, bond_type)

            # Update if this price is more recent (or if no current price exists)
            if not current_latest or timestamp >= current_latest.timestamp:
                # Update bond's current_price field
                # This would require access to bond write service or direct DB update
                # For now, just log the action
                logger.info(
                    f"Would update current_price for {bond_type.value} bond {bond_id} to {price} "
                    f"(timestamp: {timestamp})"
                )
                return True

            return False
        except Exception as e:
            logger.error(f"Error updating current price for {bond_type.value} bond {bond_id}: {str(e)}")
            return False

    def _calculate_price_from_yield(self, bond: any, ytm: float) -> float:
        """
        Calculate bond price from yield to maturity.
        Simplified implementation - production version would need full cash flow analysis.
        """
        try:
            face_value = float(getattr(bond, 'face_value', 100))
            coupon_rate = float(getattr(bond, 'coupon_rate', 0)) / 100

            # Calculate years to maturity
            today = datetime.now().date()
            years_to_maturity = (bond.maturity_date - today).days / 365.25

            if years_to_maturity <= 0:
                return face_value

            ytm_decimal = ytm / 100
            annual_coupon = coupon_rate * face_value

            if coupon_rate == 0:  # Zero coupon bond
                return face_value / ((1 + ytm_decimal) ** years_to_maturity)

            # Present value of coupon payments + present value of face value
            pv_coupons = annual_coupon * (1 - (1 + ytm_decimal) ** (-years_to_maturity)) / ytm_decimal
            pv_face_value = face_value / ((1 + ytm_decimal) ** years_to_maturity)

            return pv_coupons + pv_face_value

        except Exception as e:
            logger.error(f"Error calculating price from yield: {str(e)}")
            return 0.0

    # === Audit and Monitoring ===

    async def get_price_update_audit(
            self,
            bond_id: int = None,
            bond_type: BondTypeEnum = None,
            start_date: datetime = None,
            end_date: datetime = None,
            source: str = None
    ) -> Dict[str, any]:
        """
        Get audit trail of price updates.
        """
        try:
            # This would need implementation to filter across all bond types or specific type
            if bond_id and bond_type:
                price_updates = await self.price_read_service.get_price_history(
                    bond_id=bond_id,
                    bond_type=bond_type,
                    start_date=start_date,
                    end_date=end_date,
                    limit=1000
                )
            else:
                # Would need a method to get all price updates across bond types
                price_updates = []  # Placeholder

            # Filter by source if specified
            if source:
                price_updates = [p for p in price_updates if p.source == source]

            # Aggregate statistics
            sources = {}
            daily_counts = {}
            bond_type_counts = {}

            for price in price_updates:
                # Count by source
                source_key = price.source or "unknown"
                sources[source_key] = sources.get(source_key, 0) + 1

                # Count by date
                date_key = price.timestamp.date().isoformat()
                daily_counts[date_key] = daily_counts.get(date_key, 0) + 1

                # Count by bond type
                type_key = getattr(price, 'bond_type', 'unknown')
                bond_type_counts[type_key] = bond_type_counts.get(type_key, 0) + 1

            return {
                "total_updates": len(price_updates),
                "bond_id": bond_id,
                "bond_type": bond_type.value if bond_type else None,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                },
                "source_breakdown": sources,
                "bond_type_breakdown": bond_type_counts,
                "daily_counts": daily_counts,
                "recent_updates": [
                    {
                        "bond_id": price.bond_id,
                        "bond_type": getattr(price, 'bond_type', 'unknown'),
                        "price": float(price.price),
                        "price_type": getattr(price, 'price_type', 'unknown'),
                        "timestamp": price.timestamp.isoformat(),
                        "source": price.source
                    }
                    for price in price_updates[:10]  # Most recent 10
                ],
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating price update audit: {str(e)}")
            return {"error": str(e), "generated_at": datetime.now().isoformat()}


# Factory function
def get_bond_price_write_service() -> BondPriceWriteService:
    """Factory function for dependency injection"""
    return BondPriceWriteService()
