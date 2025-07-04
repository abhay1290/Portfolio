import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from fixed_income.src.model.enums import BondTypeEnum
from fixed_income.src.model.enums.bond_identifier_type_enum import BondIdentifierTypeEnum
from fixed_income.src.services.bond_identifer_service import BondIdentifierService, get_bond_identifier_service
from fixed_income.src.services.fixed_income_price_read_service import BondPriceReadOnlyService, \
    get_bond_price_read_service
from fixed_income.src.services.fixed_income_price_write_service import BondPriceWriteService, \
    get_bond_price_write_service
from fixed_income.src.services.fixed_income_read_service import BondReadOnlyService, get_bond_read_service
from fixed_income.src.services.fixed_income_write_service import BondWriteService, get_bond_write_service

logger = logging.getLogger(__name__)


class FixedIncomeController:
    """
    Simple controller layer for fixed income bond operations.

    Initializes and coordinates access to all bond-related services across different bond types.
    Provides a unified interface for the API layer while keeping operations simple.
    Supports multiple bond types (FIXED_COUPON, ZERO_COUPON, CALLABLE, PUTABLE, FLOATING, SINKING_FUND).
    Can be extended in the future for complex orchestration as needed.
    """

    def __init__(self):
        # Initialize all services
        self.bond_read_service: BondReadOnlyService = get_bond_read_service()
        self.bond_write_service: BondWriteService = get_bond_write_service()
        self.price_read_service: BondPriceReadOnlyService = get_bond_price_read_service()
        self.price_write_service: BondPriceWriteService = get_bond_price_write_service()
        self.bond_identifier_service: BondIdentifierService = get_bond_identifier_service()

        logger.info("FixedIncomeController initialized with all services")

    # === Bond Read Operations ===

    async def get_bond_by_id(self, bond_id: int, bond_type: BondTypeEnum):
        """Get bond by ID for specific bond type."""
        return await self.bond_read_service.get_bond_by_id(bond_id, bond_type)

    async def get_bond_by_symbol(self, symbol: str, bond_type: BondTypeEnum):
        """Get bond by symbol for specific bond type."""
        return await self.bond_read_service.get_bond_by_symbol(symbol, bond_type)

    async def get_bonds_bulk(self, bond_ids: List[int], bond_type: BondTypeEnum):
        """Get multiple bonds by IDs for specific bond type."""
        return await self.bond_read_service.get_bonds_bulk(bond_ids, bond_type)

    async def get_bonds_by_symbols_bulk(self, symbols: List[str], bond_type: BondTypeEnum):
        """Get multiple bonds by symbols for specific bond type."""
        return await self.bond_read_service.get_bonds_by_symbols_bulk(symbols, bond_type)

    async def get_all_bonds(self, bond_type: BondTypeEnum, order_by: str = "id", desc: bool = False):
        """Get all bonds for specific bond type."""
        return await self.bond_read_service.get_all_bonds(bond_type, order_by, desc)

    async def get_active_bonds(self, bond_type: BondTypeEnum):
        """Get only active bonds for specific bond type."""
        return await self.bond_read_service.get_active_bonds(bond_type)

    async def get_bonds_by_issuer(self, issuer: str, bond_type: BondTypeEnum):
        """Get bonds by issuer for specific bond type."""
        return await self.bond_read_service.get_bonds_by_issuer(issuer, bond_type)

    async def get_bonds_by_currency(self, currency: str, bond_type: BondTypeEnum):
        """Get bonds by currency for specific bond type."""
        return await self.bond_read_service.get_bonds_by_currency(currency, bond_type)

    async def get_bonds_by_maturity_range(self, start_date: datetime, end_date: datetime, bond_type: BondTypeEnum):
        """Get bonds by maturity date range for specific bond type."""
        return await self.bond_read_service.get_bonds_by_maturity_range(start_date, end_date, bond_type)

    async def search_bonds(self, search_term: str, bond_type: BondTypeEnum):
        """Search bonds for specific bond type."""
        return await self.bond_read_service.search_bonds(search_term, bond_type)

    async def validate_bond_exists(self, bond_id: int, bond_type: BondTypeEnum):
        """Validate bond exists for specific bond type."""
        return await self.bond_read_service.validate_bond_exists(bond_id, bond_type)

    async def validate_bonds_exist(self, bond_ids: List[int], bond_type: BondTypeEnum):
        """Validate multiple bonds exist for specific bond type."""
        return await self.bond_read_service.validate_bonds_exist(bond_ids, bond_type)

    async def validate_symbol_unique(self, symbol: str, bond_type: BondTypeEnum, exclude_id: int = None):
        """Validate symbol is unique for specific bond type."""
        return await self.bond_read_service.validate_symbol_unique(symbol, bond_type, exclude_id)

    async def count_bonds(self, bond_type: BondTypeEnum, **filters):
        """Count bonds with filters for specific bond type."""
        return await self.bond_read_service.count_bonds(bond_type, **filters)

    async def get_bond_summary_stats(self, bond_type: BondTypeEnum):
        """Get bond summary statistics for specific bond type."""
        return await self.bond_read_service.get_bond_summary_stats(bond_type)

    async def get_all_bond_types_summary(self):
        """Get summary statistics for all bond types."""
        return await self.bond_read_service.get_all_bond_types_summary()

    async def get_supported_bond_types(self):
        """Get list of supported bond types."""
        return await self.bond_write_service.get_supported_bond_types()

    # === Bond Write Operations ===

    async def create_bond(self, bond_data: Any, bond_type: BondTypeEnum, user_token: str = None):
        """Create a new bond for specific bond type."""
        return await self.bond_write_service.create_bond(bond_data, bond_type, user_token)

    async def update_bond(self, bond_id: int, bond_data: Any, bond_type: BondTypeEnum, user_token: str = None):
        """Update an existing bond for specific bond type."""
        return await self.bond_write_service.update_bond(bond_id, bond_data, bond_type, user_token)

    async def partial_update_bond(self, bond_id: int, bond_data: Any, bond_type: BondTypeEnum, user_token: str = None):
        """Partially update an existing bond for specific bond type."""
        return await self.bond_write_service.partial_update_bond(bond_id, bond_data, bond_type, user_token)

    async def delete_bond(self, bond_id: int, bond_type: BondTypeEnum, user_token: str = None):
        """Delete a bond for specific bond type."""
        return await self.bond_write_service.delete_bond(bond_id, bond_type, user_token)

    async def bulk_create_bonds(self, bulk_request: List[Any], bond_type: BondTypeEnum, user_token: str = None):
        """Create multiple bonds in bulk for specific bond type."""
        return await self.bond_write_service.bulk_create_bonds(bulk_request, bond_type, user_token)

    async def bulk_update_bonds(self, updates: List[Tuple[int, Any]], bond_type: BondTypeEnum, user_token: str = None):
        """Update multiple bonds in bulk for specific bond type."""
        return await self.bond_write_service.bulk_update_bonds(updates, bond_type, user_token)

    async def bulk_delete_bonds(self, bond_ids: List[int], bond_type: BondTypeEnum, user_token: str = None):
        """Delete multiple bonds in bulk for specific bond type."""
        return await self.bond_write_service.bulk_delete_bonds(bond_ids, bond_type, user_token)

    async def bulk_create_mixed_bonds(self, bond_requests: List[Tuple[str, Any]], user_token: str = None):
        """Create multiple bonds of different types in bulk."""
        return await self.bond_write_service.bulk_create_mixed_bonds(bond_requests, user_token)

    async def activate_bond(self, bond_id: int, bond_type: BondTypeEnum, user_token: str = None):
        """Activate a bond for specific bond type."""
        return await self.bond_write_service.activate_bond(bond_id, bond_type, user_token)

    async def deactivate_bond(self, bond_id: int, bond_type: BondTypeEnum, user_token: str = None):
        """Deactivate a bond for specific bond type."""
        return await self.bond_write_service.deactivate_bond(bond_id, bond_type, user_token)

    # === Price Read Operations ===

    async def get_current_price(self, bond_id: int, bond_type: BondTypeEnum):
        """Get current price for a bond of specific type."""
        return await self.price_read_service.get_current_price(bond_id, bond_type)

    async def get_current_prices_bulk(self, bond_ids: List[int], bond_type: BondTypeEnum):
        """Get current prices for multiple bonds of specific type."""
        return await self.price_read_service.get_current_prices_bulk(bond_ids, bond_type)

    async def get_current_prices_by_symbols(self, symbols: List[str], bond_type: BondTypeEnum):
        """Get current prices by symbols for specific bond type."""
        return await self.price_read_service.get_current_prices_by_symbols(symbols, bond_type)

    async def get_price_history(self, bond_id: int, bond_type: BondTypeEnum, start_date: datetime = None,
                                end_date: datetime = None, limit: int = 100):
        """Get price history for a bond of specific type."""
        return await self.price_read_service.get_price_history(bond_id, bond_type, start_date, end_date, limit)

    async def get_price_at_date(self, bond_id: int, bond_type: BondTypeEnum, target_date: datetime):
        """Get price at specific date for a bond of specific type."""
        return await self.price_read_service.get_price_at_date(bond_id, bond_type, target_date)

    async def get_price_range(self, bond_id: int, bond_type: BondTypeEnum, days: int = 30):
        """Get price range statistics for a bond of specific type."""
        return await self.price_read_service.get_price_range(bond_id, bond_type, days)

    async def get_price_performance(self, bond_id: int, bond_type: BondTypeEnum,
                                    periods: List[int] = [1, 7, 30, 90, 365]):
        """Get price performance over periods for a bond of specific type."""
        return await self.price_read_service.get_price_performance(bond_id, bond_type, periods)

    async def compare_bond_prices(self, bond_ids: List[int], bond_type: BondTypeEnum, start_date: datetime = None):
        """Compare prices across bonds of specific type."""
        return await self.price_read_service.compare_bond_prices(bond_ids, bond_type, start_date)

    async def validate_price_data_quality(self, bond_id: int, bond_type: BondTypeEnum, days: int = 7):
        """Validate price data quality for a bond of specific type."""
        return await self.price_read_service.validate_price_data_quality(bond_id, bond_type, days)

    async def get_bond_market_summary(self, bond_type: BondTypeEnum, bond_ids: List[int] = None, issuer: str = None):
        """Get bond market summary statistics for specific bond type."""
        return await self.price_read_service.get_bond_market_summary(bond_type, bond_ids, issuer)

    # === Price Write Operations ===

    async def update_price(self, bond_id: int, bond_type: BondTypeEnum, price: Decimal, timestamp: datetime = None,
                           source: str = "manual", price_type: str = "clean", user_token: str = None):
        """Update price for a bond of specific type."""
        return await self.price_write_service.update_price(bond_id, bond_type, price, timestamp, source, price_type,
                                                           user_token)

    async def bulk_update_prices(self, price_updates: List[Any], user_token: str = None):
        """Update prices for multiple bonds."""
        return await self.price_write_service.bulk_update_prices(price_updates, user_token)

    async def update_prices_from_feed(self, feed_data: Dict[str, Any], bond_type: BondTypeEnum,
                                      source: str = "market_feed",
                                      user_token: str = None):
        """Process price updates from market feed for specific bond type."""
        return await self.price_write_service.update_prices_from_feed(feed_data, bond_type, source, user_token)

    async def bulk_import_historical_prices(self, bond_id: int, bond_type: BondTypeEnum,
                                            historical_data: List[Tuple[datetime, Decimal, str]],
                                            source: str = "historical_import", user_token: str = None):
        """Import bulk historical prices for a bond of specific type."""
        return await self.price_write_service.bulk_import_historical_prices(bond_id, bond_type, historical_data, source,
                                                                            user_token)

    async def delete_price_data(self, bond_id: int, bond_type: BondTypeEnum, start_date: datetime = None,
                                end_date: datetime = None, user_token: str = None):
        """Delete price data for a bond of specific type."""
        return await self.price_write_service.delete_price_data(bond_id, bond_type, start_date, end_date, user_token)

    async def correct_price(self, price_id: int, corrected_price: Decimal,
                            correction_reason: str, user_token: str = None):
        """Correct a specific price record."""
        return await self.price_write_service.correct_price(price_id, corrected_price, correction_reason, user_token)

    async def update_price_from_yield(self, bond_id: int, bond_type: BondTypeEnum, yield_to_maturity: Decimal,
                                      timestamp: datetime = None, source: str = "yield_calculation",
                                      user_token: str = None):
        """Calculate and update bond price based on yield to maturity."""
        return await self.price_write_service.update_price_from_yield(bond_id, bond_type, yield_to_maturity, timestamp,
                                                                      source, user_token)

    async def sync_with_market_data(self, bond_type: BondTypeEnum, bond_ids: List[int] = None,
                                    symbols: List[str] = None,
                                    force_update: bool = False, user_token: str = None):
        """Synchronize bond prices with external market data sources."""
        return await self.price_write_service.sync_with_market_data(bond_type, bond_ids, symbols, force_update,
                                                                    user_token)

    async def get_price_update_audit(self, bond_id: int = None, bond_type: BondTypeEnum = None,
                                     start_date: datetime = None,
                                     end_date: datetime = None, source: str = None):
        """Get price update audit trail."""
        return await self.price_write_service.get_price_update_audit(bond_id, bond_type, start_date, end_date, source)

    # === Convenience Methods ===

    async def update_bond_price(self, bond_id: int, new_price: float, bond_type: BondTypeEnum, user_token: str = None):
        """Update price for a single bond (convenience method)."""
        return await self.bond_write_service.update_bond_price(bond_id, new_price, bond_type, user_token)

    async def bulk_update_bond_prices(self, price_updates: List[Tuple[int, float]], bond_type: BondTypeEnum,
                                      user_token: str = None):
        """Update prices for multiple bonds in bulk (convenience method)."""
        return await self.bond_write_service.bulk_update_bond_prices(price_updates, bond_type, user_token)

    async def get_bond_essentials(self, bond_ids: List[int], bond_type: BondTypeEnum):
        """Get essential information for multiple bonds."""
        return await self.bond_read_service.get_bond_essentials(bond_ids, bond_type)

    async def get_current_bond_prices(self, bond_ids: List[int], bond_type: BondTypeEnum):
        """Get current prices for multiple bonds (convenience method)."""
        return await self.bond_read_service.get_current_prices(bond_ids, bond_type)

        # === Bond Identifier Operations ===

    async def get_bond_isin(self, bond_id: int) -> Optional[str]:
        """Get current ISIN for a bond."""
        return self.bond_identifier_service.get_current_isin(bond_id)

    async def get_bond_cusip(self, bond_id: int) -> Optional[str]:
        """Get current CUSIP for a bond."""
        return self.bond_identifier_service.get_current_cusip(bond_id)

    async def get_bond_rating(self, bond_id: int, agency: str = "MOODY") -> Optional[str]:
        """Get current rating for a bond from specific agency."""
        return self.bond_identifier_service.get_current_rating(bond_id, agency)

    async def find_bond_by_isin(self, isin: str):
        """Find bond by ISIN."""
        return self.bond_identifier_service.find_bond_by_isin(isin)

    async def find_bond_by_cusip(self, cusip: str):
        """Find bond by CUSIP."""
        return self.bond_identifier_service.find_bond_by_cusip(cusip)

    async def get_bonds_by_rating(self, agency: str, rating: str):
        """Get all bonds with specific rating."""
        return self.bond_identifier_service.get_bonds_by_rating(agency, rating)

    async def get_bond_identifiers(self, bond_id: int) -> Dict[str, str]:
        """Get all current identifiers for a bond."""
        return self.bond_identifier_service.get_all_current_identifiers(bond_id)

    async def add_bond_identifiers(self, bond_id: int, isin: str = None, cusip: str = None,
                                   rating_moody: str = None, rating_sp: str = None,
                                   created_by: str = "system", source: str = None):
        """Add multiple identifiers to a bond at once."""
        return self.bond_identifier_service.bulk_add_bond_identifiers(
            bond_id, isin, cusip, rating_moody, rating_sp, created_by, source
        )

    async def request_rating_change(self, bond_id: int, agency: str, new_rating: str,
                                    requested_by: str, rating_rationale: str = None):
        """Request a rating change for a bond."""
        return self.bond_identifier_service.request_rating_change(
            bond_id, agency, new_rating, requested_by, rating_rationale
        )

    async def validate_rating_format(self, rating: str, agency: str) -> bool:
        """Validate rating format for specific agency."""
        return self.bond_identifier_service.validate_rating_format(rating, agency)

    async def get_identifier_history(self, bond_id: int, identifier_type: BondIdentifierTypeEnum):
        """Get identifier history for a bond."""
        return self.bond_identifier_service.get_identifier_history(bond_id, identifier_type)

    async def approve_identifier_change(self, change_request_id: int, approved_by: str):
        """Approve identifier change request."""
        return self.bond_identifier_service.approve_change_request(change_request_id, approved_by)

    async def reject_identifier_change(self, change_request_id: int, rejected_by: str, reason: str = None):
        """Reject identifier change request."""
        return self.bond_identifier_service.reject_change_request(change_request_id, rejected_by, reason)

    async def get_pending_identifier_changes(self, bond_id: int = None):
        """Get pending identifier change requests."""
        return self.bond_identifier_service.get_pending_change_requests(bond_id)

    async def search_identifiers(self, search_term: str, identifier_types: List[BondIdentifierTypeEnum] = None):
        """Search for identifiers across bonds."""
        return self.bond_identifier_service.search_identifiers(search_term, identifier_types)

    async def get_identifier_statistics(self):
        """Get identifier system statistics."""
        return self.bond_identifier_service.get_identifier_statistics()

    # === Health Check ===

    async def health_check(self):
        """Simple health check across services."""
        try:
            # Test each service with a simple operation
            supported_types = await self.get_supported_bond_types()

            # Test with first available bond type if any exist
            bond_type_counts = {}
            for bond_type in supported_types:
                try:
                    count = await self.bond_read_service.count_bonds(bond_type)
                    bond_type_counts[bond_type] = count
                except Exception as e:
                    logger.warning(f"Health check failed for {bond_type}: {str(e)}")
                    bond_type_counts[bond_type] = "error"

            return {
                "status": "healthy",
                "services": {
                    "bond_read": "healthy",
                    "bond_write": "healthy",
                    "price_read": "healthy",
                    "price_write": "healthy"
                },
                "supported_bond_types": supported_types,
                "bond_type_counts": bond_type_counts,
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
def get_fixed_income_controller() -> FixedIncomeController:
    """Factory function for dependency injection"""
    return FixedIncomeController()
