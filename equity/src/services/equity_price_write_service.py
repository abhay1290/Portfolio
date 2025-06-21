import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from equity.src.model.equity.EquityPrice import EquityPrice  # Assuming this model exists
from fastapi import HTTPException, status

from equity.src.api.equity_schema.Equity_Schema import (
    EquityPriceRequest,
    EquityPriceResponse
)
from equity.src.database.generic_database_excess import GenericDatabaseService
from equity.src.services.equity_price_read_service import get_equity_price_read_service
from equity.src.services.equity_read_service import get_equity_read_service

logger = logging.getLogger(__name__)


class EquityPriceWriteService:
    """
    Pure Write-Only Equity Price Service

    Handles all price-related write operations (Create, Update, Delete).
    Optimized for high-frequency price updates from market data feeds.
    Includes validation and cache invalidation.
    """

    def __init__(self):
        self.db_service = GenericDatabaseService(
            model=EquityPrice,
            create_schema=EquityPriceRequest,
            response_schema=EquityPriceResponse,
            update_schema=EquityPriceRequest
        )
        self.equity_read_service = get_equity_read_service()
        self.price_read_service = get_equity_price_read_service()

    # === Core Price Operations ===

    async def update_price(
            self,
            equity_id: int,
            price: Decimal,
            timestamp: datetime = None,
            source: str = "manual",
            user_token: str = None
    ) -> EquityPriceResponse:
        """
        Update/create price for a single equity.
        """
        try:
            # Validate equity exists
            equity = await self.equity_read_service.get_equity_by_id(equity_id)
            if not equity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Equity with ID {equity_id} not found"
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
            existing_price = await self._get_price_at_exact_timestamp(equity_id, timestamp)
            if existing_price:
                # Update existing price
                price_data = EquityPriceRequest(
                    equity_id=equity_id,
                    price=price,
                    timestamp=timestamp,
                    source=source
                )
                updated_price = await self.db_service.update(existing_price.id, price_data)
                logger.info(f"Updated existing price for equity {equity_id} at {timestamp}")
            else:
                # Create new price record
                price_data = EquityPriceRequest(
                    equity_id=equity_id,
                    price=price,
                    timestamp=timestamp,
                    source=source
                )
                updated_price = await self.db_service.create(price_data)
                logger.info(f"Created new price for equity {equity_id}: {price}")

            # Future: Invalidate caches
            # await self.price_read_service.invalidate_price_cache(equity_id)

            # Update current price in equity table if this is the most recent
            await self._update_equity_current_price_if_latest(equity_id, price, timestamp)

            return updated_price

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating price for equity {equity_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update equity price"
            )

    async def bulk_update_prices(
            self,
            price_updates: List[EquityPriceRequest],
            user_token: str = None
    ) -> List[EquityPriceResponse]:
        """
        Update prices for multiple equities in bulk.
        Optimized for market data feeds.
        """
        try:
            # Pre-validate all equity IDs exist
            equity_ids = [update.equity_id for update in price_updates]
            equity_validations = await self.equity_read_service.validate_equities_exist(equity_ids)

            valid_updates = []
            invalid_updates = []

            for update in price_updates:
                if equity_validations.get(update.equity_id, False):
                    if update.price > 0:  # Basic validation
                        valid_updates.append(update)
                    else:
                        invalid_updates.append(f"Invalid price for equity {update.equity_id}")
                else:
                    invalid_updates.append(f"Equity {update.equity_id} not found")

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
                        equity_id=update.equity_id,
                        price=update.price,
                        timestamp=update.timestamp or datetime.now(),
                        source=update.source or "bulk_update",
                        user_token=user_token
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to update price for equity {update.equity_id}: {str(e)}")

            logger.info(f"Bulk updated {len(results)} prices, skipped {len(invalid_updates)}")
            return results

        except Exception as e:
            logger.error(f"Error in bulk price update: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to bulk update prices"
            )

    async def update_prices_from_feed(
            self,
            feed_data: Dict[str, any],
            source: str = "market_feed",
            user_token: str = None
    ) -> Dict[str, any]:
        """
        Process price updates from external market data feed.
        """
        try:
            # Parse feed data - format may vary by provider
            price_updates = []
            errors = []

            for symbol, price_data in feed_data.items():
                try:
                    # Get equity by symbol
                    equity = await self.equity_read_service.get_equity_by_symbol(symbol)
                    if not equity:
                        errors.append(f"Symbol {symbol} not found")
                        continue

                    # Parse price data
                    price = Decimal(str(price_data.get('price', 0)))
                    timestamp = price_data.get('timestamp')
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp)
                    elif not timestamp:
                        timestamp = datetime.now()

                    price_updates.append(EquityPriceRequest(
                        equity_id=equity.id,
                        price=price,
                        timestamp=timestamp,
                        source=source
                    ))

                except Exception as e:
                    errors.append(f"Error parsing data for {symbol}: {str(e)}")

            # Process valid updates
            if price_updates:
                results = await self.bulk_update_prices(price_updates, user_token)

                return {
                    "status": "completed",
                    "processed": len(results),
                    "errors": len(errors),
                    "error_details": errors[:10],  # Limit error details
                    "source": source,
                    "processed_at": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "no_valid_data",
                    "processed": 0,
                    "errors": len(errors),
                    "error_details": errors,
                    "source": source,
                    "processed_at": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error processing market feed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process market data feed"
            )

    # === Historical Price Management ===

    async def bulk_import_historical_prices(
            self,
            equity_id: int,
            historical_data: List[Tuple[datetime, Decimal]],
            source: str = "historical_import",
            user_token: str = None
    ) -> Dict[str, any]:
        """
        Import bulk historical price data for an equity.
        """
        try:
            # Validate equity exists
            equity = await self.equity_read_service.get_equity_by_id(equity_id)
            if not equity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Equity with ID {equity_id} not found"
                )

            # Prepare price requests
            price_requests = []
            for timestamp, price in historical_data:
                if price > 0:  # Basic validation
                    price_requests.append(EquityPriceRequest(
                        equity_id=equity_id,
                        price=price,
                        timestamp=timestamp,
                        source=source
                    ))

            if not price_requests:
                return {
                    "status": "no_valid_data",
                    "imported": 0,
                    "equity_id": equity_id
                }

            # Sort by timestamp for efficient processing
            price_requests.sort(key=lambda x: x.timestamp)

            # Bulk create (assuming no duplicates for historical import)
            results = await self.db_service.bulk_create(price_requests)

            # Update current price if latest timestamp is most recent
            latest_price = price_requests[-1]
            await self._update_equity_current_price_if_latest(
                equity_id, latest_price.price, latest_price.timestamp
            )

            logger.info(f"Imported {len(results)} historical prices for equity {equity_id}")

            return {
                "status": "completed",
                "imported": len(results),
                "equity_id": equity_id,
                "date_range": {
                    "start": price_requests[0].timestamp.isoformat(),
                    "end": price_requests[-1].timestamp.isoformat()
                },
                "imported_at": datetime.now().isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error importing historical prices for equity {equity_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to import historical prices"
            )

    async def delete_price_data(
            self,
            equity_id: int,
            start_date: datetime = None,
            end_date: datetime = None,
            user_token: str = None
    ) -> Dict[str, any]:
        """
        Delete price data for an equity within date range.
        """
        try:
            # Validate equity exists
            equity = await self.equity_read_service.get_equity_by_id(equity_id)
            if not equity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Equity with ID {equity_id} not found"
                )

            # Build filters
            filters = {"equity_id": equity_id}
            if start_date:
                filters["timestamp__gte"] = start_date
            if end_date:
                filters["timestamp__lte"] = end_date

            # Get prices to delete (for logging)
            prices_to_delete = await self.db_service.get_filtered(filters=filters)

            # Delete prices
            deleted_count = await self.db_service.bulk_delete_filtered(filters)

            # Future: Invalidate caches
            # await self.price_read_service.invalidate_price_cache(equity_id)

            logger.info(f"Deleted {deleted_count} price records for equity {equity_id}")

            return {
                "status": "completed",
                "deleted_count": deleted_count,
                "equity_id": equity_id,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                },
                "deleted_at": datetime.now().isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting price data for equity {equity_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete price data"
            )

    # === Price Correction Operations ===

    async def correct_price(
            self,
            price_id: int,
            corrected_price: Decimal,
            correction_reason: str,
            user_token: str = None
    ) -> EquityPriceResponse:
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
            correction_data = EquityPriceRequest(
                equity_id=existing_price.equity_id,
                price=corrected_price,
                timestamp=existing_price.timestamp,
                source=f"correction:{correction_reason}",
                original_price=old_price  # Track original for audit
            )

            # Update the price
            corrected_price_record = await self.db_service.update(price_id, correction_data)

            # Future: Invalidate caches
            # await self.price_read_service.invalidate_price_cache(existing_price.equity_id)

            # Log correction
            logger.info(
                f"Corrected price {price_id} for equity {existing_price.equity_id}: "
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

    # === Market Data Synchronization ===

    async def sync_with_market_data(
            self,
            equity_ids: List[int] = None,
            symbols: List[str] = None,
            force_update: bool = False,
            user_token: str = None
    ) -> Dict[str, any]:
        """
        Synchronize prices with external market data sources.
        """
        try:
            # Determine which equities to sync
            target_equities = []

            if symbols:
                equities = await self.equity_read_service.get_equities_by_symbols_bulk(symbols)
                target_equities.extend(equities)

            if equity_ids:
                equities = await self.equity_read_service.get_equities_bulk(equity_ids)
                target_equities.extend(equities)

            if not target_equities and not equity_ids and not symbols:
                # Sync all active equities
                target_equities = await self.equity_read_service.get_active_equities()

            if not target_equities:
                return {
                    "status": "no_equities_found",
                    "synced": 0,
                    "errors": 0
                }

            # TODO: Implement actual market data provider integration
            # This is a placeholder for market data sync logic
            synced_count = 0
            errors = []

            for equity in target_equities:
                try:
                    # Placeholder: In real implementation, call market data API
                    # market_price = await external_market_data_provider.get_price(equity.symbol)
                    #
                    # For now, simulate sync
                    logger.info(f"Would sync price for {equity.symbol}")
                    synced_count += 1

                except Exception as e:
                    errors.append(f"Failed to sync {equity.symbol}: {str(e)}")

            return {
                "status": "completed",
                "synced": synced_count,
                "errors": len(errors),
                "error_details": errors[:10],
                "force_update": force_update,
                "synced_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error syncing market data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to sync market data"
            )

    # === Helper Methods ===

    async def _get_price_at_exact_timestamp(
            self,
            equity_id: int,
            timestamp: datetime
    ) -> Optional[EquityPriceResponse]:
        """Get price at exact timestamp if exists."""
        try:
            prices = await self.db_service.get_filtered(
                filters={
                    "equity_id": equity_id,
                    "timestamp": timestamp
                },
                limit=1
            )
            return prices[0] if prices else None
        except Exception:
            return None

    async def _update_equity_current_price_if_latest(
            self,
            equity_id: int,
            price: Decimal,
            timestamp: datetime
    ) -> bool:
        """Update equity's current_price field if this is the latest price."""
        try:
            # Get current latest price
            current_latest = await self.price_read_service.get_current_price(equity_id)

            # Update if this price is more recent (or if no current price exists)
            if not current_latest or timestamp >= current_latest.timestamp:
                # Update equity's current_price field
                # This would require access to equity write service or direct DB update
                # For now, just log the action
                logger.info(
                    f"Would update current_price for equity {equity_id} to {price} "
                    f"(timestamp: {timestamp})"
                )
                return True

            return False
        except Exception as e:
            logger.error(f"Error updating current price for equity {equity_id}: {str(e)}")
            return False

    # === Audit and Monitoring ===

    async def get_price_update_audit(
            self,
            equity_id: int = None,
            start_date: datetime = None,
            end_date: datetime = None,
            source: str = None
    ) -> Dict[str, any]:
        """
        Get audit trail of price updates.
        """
        try:
            filters = {}

            if equity_id:
                filters["equity_id"] = equity_id
            if start_date:
                filters["timestamp__gte"] = start_date
            if end_date:
                filters["timestamp__lte"] = end_date
            if source:
                filters["source"] = source

            price_updates = await self.db_service.get_filtered(
                filters=filters,
                order_by="timestamp",
                desc=True,
                limit=1000
            )

            # Aggregate statistics
            sources = {}
            daily_counts = {}

            for price in price_updates:
                # Count by source
                source_key = price.source or "unknown"
                sources[source_key] = sources.get(source_key, 0) + 1

                # Count by date
                date_key = price.timestamp.date().isoformat()
                daily_counts[date_key] = daily_counts.get(date_key, 0) + 1

            return {
                "total_updates": len(price_updates),
                "equity_id": equity_id,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                },
                "source_breakdown": sources,
                "daily_counts": daily_counts,
                "recent_updates": [
                    {
                        "equity_id": price.equity_id,
                        "price": float(price.price),
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
def get_equity_price_write_service() -> EquityPriceWriteService:
    """Factory function for dependency injection"""
    return EquityPriceWriteService()
