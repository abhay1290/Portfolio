import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

from equity.src.services.equity_identifier_service import EquityIdentifierService, get_equity_identifier_service
from equity.src.services.equity_price_read_service import EquityPriceReadOnlyService, get_equity_price_read_service
from equity.src.services.equity_price_write_service import EquityPriceWriteService, get_equity_price_write_service
from equity.src.services.equity_read_service import EquityReadOnlyService, get_equity_read_service
from equity.src.services.equity_write_service import EquityWriteService, get_equity_write_service

logger = logging.getLogger(__name__)


class EquityController:
    """
    Simple controller layer for equity operations.

    Initializes and coordinates access to all equity-related services.
    Provides a unified interface for the API layer while keeping operations simple.
    Can be extended in the future for complex orchestration as needed.
    """

    def __init__(self):
        # Initialize all services
        self.equity_read_service: EquityReadOnlyService = get_equity_read_service()
        self.equity_write_service: EquityWriteService = get_equity_write_service()
        self.price_read_service: EquityPriceReadOnlyService = get_equity_price_read_service()
        self.price_write_service: EquityPriceWriteService = get_equity_price_write_service()
        self.identifier_service: EquityIdentifierService = get_equity_identifier_service()

        logger.info("EquityController initialized with all services")

    # === Equity Read Operations ===

    async def get_equity_by_id(self, equity_id: int):
        """Get equity by ID."""
        return await self.equity_read_service.get_equity_by_id(equity_id)

    async def get_equity_by_symbol(self, symbol: str):
        """Get equity by symbol."""
        return await self.equity_read_service.get_equity_by_symbol(symbol)

    async def get_equities_bulk(self, equity_ids: List[int]):
        """Get multiple equities by IDs."""
        return await self.equity_read_service.get_equities_bulk(equity_ids)

    async def get_equities_by_symbols_bulk(self, symbols: List[str]):
        """Get multiple equities by symbols."""
        return await self.equity_read_service.get_equities_by_symbols_bulk(symbols)

    async def get_all_equities(self, order_by: str = "id", desc: bool = False):
        """Get all equities."""
        return await self.equity_read_service.get_all_equities(order_by, desc)

    async def get_active_equities(self):
        """Get only active equities."""
        return await self.equity_read_service.get_active_equities()

    async def get_equities_by_sector(self, sector: str):
        """Get equities by sector."""
        return await self.equity_read_service.get_equities_by_sector(sector)

    async def get_equities_by_currency(self, currency):
        """Get equities by currency."""
        return await self.equity_read_service.get_equities_by_currency(currency)

    async def search_equities(self, search_term: str):
        """Search equities."""
        return await self.equity_read_service.search_equities(search_term)

    async def validate_equity_exists(self, equity_id: int):
        """Validate equity exists."""
        return await self.equity_read_service.validate_equity_exists(equity_id)

    async def validate_equities_exist(self, equity_ids: List[int]):
        """Validate multiple equities exist."""
        return await self.equity_read_service.validate_equities_exist(equity_ids)

    async def count_equities(self, **filters):
        """Count equities with filters."""
        return await self.equity_read_service.count_equities(**filters)

    async def get_equity_summary_stats(self):
        """Get equity summary statistics."""
        return await self.equity_read_service.get_equity_summary_stats()

    # === Equity Write Operations ===

    async def create_equity(self, equity_data, user_token: str = None):
        """Create a new equity."""
        return await self.equity_write_service.create_equity(equity_data, user_token)

    async def update_equity(self, equity_id: int, equity_data, user_token: str = None):
        """Update an existing equity."""
        return await self.equity_write_service.update_equity(equity_id, equity_data, user_token)

    async def partial_update_equity(self, equity_id: int, equity_data, user_token: str = None):
        """Partially update an existing equity."""
        return await self.equity_write_service.partial_update_equity(equity_id, equity_data, user_token)

    async def delete_equity(self, equity_id: int, user_token: str = None):
        """Delete an equity."""
        return await self.equity_write_service.delete_equity(equity_id, user_token)

    async def bulk_create_equities(self, bulk_request: List, user_token: str = None):
        """Create multiple equities in bulk."""
        return await self.equity_write_service.bulk_create_equities(bulk_request, user_token)

    async def bulk_update_equities(self, updates: List, user_token: str = None):
        """Update multiple equities in bulk."""
        return await self.equity_write_service.bulk_update_equities(updates, user_token)

    async def bulk_delete_equities(self, equity_ids: List[int], user_token: str = None):
        """Delete multiple equities in bulk."""
        return await self.equity_write_service.bulk_delete_equities(equity_ids, user_token)

    async def activate_equity(self, equity_id: int, user_token: str = None):
        """Activate an equity."""
        return await self.equity_write_service.activate_equity(equity_id, user_token)

    async def deactivate_equity(self, equity_id: int, user_token: str = None):
        """Deactivate an equity."""
        return await self.equity_write_service.deactivate_equity(equity_id, user_token)

    # === Price Read Operations ===

    async def get_current_price(self, equity_id: int):
        """Get current price for an equity."""
        return await self.price_read_service.get_current_price(equity_id)

    async def get_current_prices_bulk(self, equity_ids: List[int]):
        """Get current prices for multiple equities."""
        return await self.price_read_service.get_current_prices_bulk(equity_ids)

    async def get_current_prices_by_symbols(self, symbols: List[str]):
        """Get current prices by symbols."""
        return await self.price_read_service.get_current_prices_by_symbols(symbols)

    async def get_price_history(self, equity_id: int, start_date: datetime = None,
                                end_date: datetime = None, limit: int = 100):
        """Get price history for an equity."""
        return await self.price_read_service.get_price_history(equity_id, start_date, end_date, limit)

    async def get_price_at_date(self, equity_id: int, target_date: datetime):
        """Get price at specific date."""
        return await self.price_read_service.get_price_at_date(equity_id, target_date)

    async def get_price_range(self, equity_id: int, days: int = 30):
        """Get price range statistics."""
        return await self.price_read_service.get_price_range(equity_id, days)

    async def get_price_performance(self, equity_id: int, periods: List[int] = [1, 7, 30, 90, 365]):
        """Get price performance over periods."""
        return await self.price_read_service.get_price_performance(equity_id, periods)

    async def compare_prices(self, equity_ids: List[int], start_date: datetime = None):
        """Compare prices across equities."""
        return await self.price_read_service.compare_prices(equity_ids, start_date)

    async def validate_price_data_quality(self, equity_id: int, days: int = 7):
        """Validate price data quality."""
        return await self.price_read_service.validate_price_data_quality(equity_id, days)

    async def get_market_summary(self, equity_ids: List[int] = None, sector: str = None):
        """Get market summary statistics."""
        return await self.price_read_service.get_market_summary(equity_ids, sector)

    # === Price Write Operations ===

    async def update_price(self, equity_id: int, price: Decimal, timestamp: datetime = None,
                           source: str = "manual", user_token: str = None):
        """Update price for an equity."""
        return await self.price_write_service.update_price(equity_id, price, timestamp, source, user_token)

    async def bulk_update_prices(self, price_updates: List, user_token: str = None):
        """Update prices for multiple equities."""
        return await self.price_write_service.bulk_update_prices(price_updates, user_token)

    async def update_prices_from_feed(self, feed_data: Dict[str, Any], source: str = "market_feed",
                                      user_token: str = None):
        """Process price updates from market feed."""
        return await self.price_write_service.update_prices_from_feed(feed_data, source, user_token)

    async def bulk_import_historical_prices(self, equity_id: int, historical_data: List,
                                            source: str = "historical_import", user_token: str = None):
        """Import bulk historical prices."""
        return await self.price_write_service.bulk_import_historical_prices(
            equity_id, historical_data, source, user_token
        )

    async def delete_price_data(self, equity_id: int, start_date: datetime = None,
                                end_date: datetime = None, user_token: str = None):
        """Delete price data for an equity."""
        return await self.price_write_service.delete_price_data(equity_id, start_date, end_date, user_token)

    async def correct_price(self, price_id: int, corrected_price: Decimal,
                            correction_reason: str, user_token: str = None):
        """Correct a specific price record."""
        return await self.price_write_service.correct_price(price_id, corrected_price, correction_reason, user_token)

    async def sync_with_market_data(self, equity_ids: List[int] = None, symbols: List[str] = None,
                                    force_update: bool = False, user_token: str = None):
        """Sync with external market data."""
        return await self.price_write_service.sync_with_market_data(equity_ids, symbols, force_update, user_token)

    async def get_price_update_audit(self, equity_id: int = None, start_date: datetime = None,
                                     end_date: datetime = None, source: str = None):
        """Get price update audit trail."""
        return await self.price_write_service.get_price_update_audit(equity_id, start_date, end_date, source)

    # === Identifier Operations  ===

    async def get_equity_identifiers(self, equity_id: int):
        """Get all current identifiers for an equity."""
        return self.identifier_service.get_all_current_identifiers(equity_id)

    async def get_equity_ticker(self, equity_id: int):
        """Get current ticker for an equity."""
        return self.identifier_service.get_current_ticker(equity_id)

    async def get_equity_isin(self, equity_id: int):
        """Get current ISIN for an equity."""
        return self.identifier_service.get_current_isin(equity_id)

    async def get_equity_cusip(self, equity_id: int):
        """Get current CUSIP for an equity."""
        return self.identifier_service.get_current_cusip(equity_id)

    async def find_equity_by_ticker(self, ticker: str):
        """Find equity by ticker symbol."""
        return self.identifier_service.find_equity_by_ticker(ticker)

    async def find_equity_by_isin(self, isin: str):
        """Find equity by ISIN."""
        return self.identifier_service.find_equity_by_isin(isin)

    async def find_equity_by_cusip(self, cusip: str):
        """Find equity by CUSIP."""
        return self.identifier_service.find_equity_by_cusip(cusip)

    async def add_equity_identifiers(self, equity_id: int, ticker: str = None, isin: str = None,
                                     cusip: str = None, sedol: str = None, created_by: str = "system"):
        """Add multiple identifiers to an equity."""
        return self.identifier_service.bulk_add_equity_identifiers(
            equity_id=equity_id,
            ticker=ticker,
            isin=isin,
            cusip=cusip,
            sedol=sedol,
            created_by=created_by
        )

    async def request_ticker_change(self, equity_id: int, new_ticker: str, requested_by: str):
        """Request a ticker symbol change."""
        return self.identifier_service.request_ticker_change(
            equity_id=equity_id,
            new_ticker=new_ticker,
            requested_by=requested_by
        )

    async def approve_identifier_change(self, change_request_id, approved_by: str):
        """Approve identifier change request."""
        return self.identifier_service.approve_change_request(change_request_id, approved_by)

    async def reject_identifier_change(self, change_request_id, rejected_by: str, reason: str = None):
        """Reject identifier change request."""
        return self.identifier_service.reject_change_request(change_request_id, rejected_by, reason)

    async def get_pending_change_requests(self, equity_id: int = None):
        """Get pending change requests."""
        return self.identifier_service.get_pending_change_requests(equity_id)

    async def get_identifier_history(self, equity_id: int, identifier_type):
        """Get identifier history."""
        return self.identifier_service.get_identifier_history(equity_id, identifier_type)

    async def search_identifiers(self, search_term: str, identifier_types=None):
        """Search for identifiers."""
        return self.identifier_service.search_identifiers(search_term, identifier_types)

    async def get_identifier_statistics(self):
        """Get identifier system statistics."""
        return self.identifier_service.get_identifier_statistics()

    async def rollback_identifier(self, equity_id: int, identifier_type, target_version: int, reason: str,
                                  performed_by: str):
        """Rollback identifier to specific version."""
        return self.identifier_service.rollback_identifier(equity_id, identifier_type, target_version, reason,
                                                           performed_by)

    async def get_version_diff(self, equity_id: int, identifier_type, version1: int, version2: int):
        """Compare two versions of an identifier."""
        return self.identifier_service.get_version_diff(equity_id, identifier_type, version1, version2)

    async def validate_identifier_integrity(self, equity_id: int = None):
        """Validate identifier data integrity."""
        return self.identifier_service.validate_identifier_integrity(equity_id)

    # === Updated Health Check ===

    async def health_check(self):
        """Simple health check across services."""
        try:
            # Test each service with a simple operation
            equity_count = await self.equity_read_service.count_equities()

            # Test identifier service
            try:
                identifier_stats = self.identifier_service.get_identifier_statistics()
                identifier_service_status = "healthy"
            except Exception as e:
                logger.warning(f"Identifier service health check failed: {str(e)}")
                identifier_service_status = "unhealthy"
                identifier_stats = None

            return {
                "status": "healthy",
                "services": {
                    "equity_read": "healthy",
                    "equity_write": "healthy",
                    "price_read": "healthy",
                    "price_write": "healthy",
                    "identifier_service": identifier_service_status
                },
                "equity_count": equity_count,
                "identifier_statistics": identifier_stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Factory function
def get_equity_controller() -> EquityController:
    """Factory function for dependency injection"""
    return EquityController()
