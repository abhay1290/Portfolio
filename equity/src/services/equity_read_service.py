import datetime
import logging
from typing import Any, Dict, List, Optional

from equity.src.api.equity_schema.Equity_Schema import EquityRequest, EquityResponse
from equity.src.database.equity_database_service import EquityDatabaseService
from equity.src.model.enums.CurrencyEnum import CurrencyEnum
from equity.src.model.equity.Equity import Equity

logger = logging.getLogger(__name__)


class EquityReadOnlyService:
    """
    Pure Read-Only Equity Service

    Handles all read operations with future caching support.
    No write operations - completely focused on data retrieval and validation.
    Optimized for high-performance lookups and bulk operations.
    """

    def __init__(self):
        self.db_service = EquityDatabaseService(
            model=Equity,
            create_schema=EquityRequest,  # Required for type consistency
            response_schema=EquityResponse
        )
        # Future: self.cache = RedisCache() or MemcachedCache()

    # === Core Read Operations ===

    async def get_equity_by_id(self, equity_id: int) -> Optional[EquityResponse]:
        """
        Get equity by ID with future caching support.
        """
        try:
            # Future: Check cache first
            # cached = await self.cache.get(f"equity:{equity_id}")
            # if cached: return EquityResponse.parse_raw(cached)

            equity = await self.db_service.get_by_id(equity_id)

            # Future: Cache the result
            # if equity: await self.cache.setex(f"equity:{equity_id}", 3600, equity.json())

            return equity
        except Exception as e:
            logger.error(f"Error getting equity by ID {equity_id}: {str(e)}")
            return None

    async def get_equity_by_symbol(self, symbol: str) -> Optional[EquityResponse]:
        """
        Get equity by symbol with future caching support.
        """
        try:
            # Future: Check cache first
            # cached = await self.cache.get(f"equity:symbol:{symbol}")
            # if cached: return EquityResponse.parse_raw(cached)

            equities = await self.db_service.get_by_column("symbol", symbol)
            equity = equities[0] if equities else None

            # Future: Cache the result
            # if equity: await self.cache.setex(f"equity:symbol:{symbol}", 3600, equity.json())

            return equity
        except Exception as e:
            logger.error(f"Error getting equity by symbol {symbol}: {str(e)}")
            return None

    async def get_equities_bulk(self, equity_ids: List[int]) -> List[EquityResponse]:
        """
        Bulk equity retrieval with optimized queries and future caching.
        """
        try:
            # Future: Check cache for each ID first, only query missing ones
            return await self.db_service.get_by_ids(equity_ids)
        except Exception as e:
            logger.error(f"Error in bulk equity retrieval: {str(e)}")
            return []

    async def get_equities_by_symbols_bulk(self, symbols: List[str]) -> List[EquityResponse]:
        """
        Optimized bulk equity retrieval by symbols using single query.
        """
        try:
            # Use a single database query instead of multiple individual queries
            return await self.db_service.get_by_column("symbol", symbols)
        except Exception as e:
            logger.error(f"Error in bulk symbol retrieval: {str(e)}")
            return []

    async def get_all_equities(
            self,
            order_by: str = "id",
            desc: bool = False
    ) -> List[EquityResponse]:
        """
        Get all equities with pagination and ordering.
        """
        try:
            return await self.db_service.get_all(order_by=order_by, desc=desc)
        except Exception as e:
            logger.error(f"Error getting all equities: {str(e)}")
            return []

    # === Filtered Read Operations ===

    async def get_active_equities(
            self,
    ) -> List[EquityResponse]:
        """
        Get only active equities.
        """
        try:
            # Future: Cache active equity list with shorter TTL
            return await self.db_service.get_by_column("is_active", True)
        except Exception as e:
            logger.error(f"Error getting active equities: {str(e)}")
            return []

    async def get_equities_by_sector(
            self,
            sector: str,
    ) -> List[EquityResponse]:
        """
        Get equities by sector.
        """
        try:
            return await self.db_service.get_by_column("sector", sector)
        except Exception as e:
            logger.error(f"Error getting equities by sector {sector}: {str(e)}")
            return []

    async def get_equities_by_currency(
            self,
            currency: CurrencyEnum,
    ) -> List[EquityResponse]:
        """
        Get equities by currency.
        """
        try:
            return await self.db_service.get_by_column("currency", currency)
        except Exception as e:
            logger.error(f"Error getting equities by currency {currency}: {str(e)}")
            return []

    # === Search Operations ===

    async def search_equities(
            self,
            search_term: str
    ) -> List[EquityResponse]:
        """
        Search equities across multiple columns.
        """
        try:
            search_columns = ["symbol", "company_name", "sector"]
            return await self.db_service.search(search_term, search_columns)
        except Exception as e:
            logger.error(f"Error searching equities with term '{search_term}': {str(e)}")
            return []

    # === Validation Operations ===

    async def validate_equity_exists(self, equity_id: int) -> bool:
        """
        Validate that an equity exists by ID.
        """
        try:
            # Future: Check cache first for faster validation
            return await self.db_service.exists(equity_id)
        except Exception as e:
            logger.error(f"Error validating equity {equity_id}: {str(e)}")
            return False

    async def validate_equities_exist(self, equity_ids: List[int]) -> Dict[int, bool]:
        """
        Validate multiple equities exist.
        """
        try:
            results = {}
            for equity_id in equity_ids:
                results[equity_id] = await self.validate_equity_exists(equity_id)
            return results
        except Exception as e:
            logger.error(f"Error validating equities exist: {str(e)}")
            return {equity_id: False for equity_id in equity_ids}

    async def validate_symbol_unique(self, symbol: str, exclude_id: int = None) -> bool:
        """
        Validate that a symbol is unique (doesn't already exist).

        Args:
            symbol: Symbol to check
            exclude_id: Optional equity ID to exclude from check (for updates)

        Returns:
            True if symbol is unique, False if duplicate exists
        """
        try:
            existing_equity = await self.get_equity_by_symbol(symbol)
            if not existing_equity:
                return True

            # If exclude_id provided, check if found equity is the same one being updated
            if exclude_id and existing_equity.id == exclude_id:
                return True

            return False
        except Exception as e:
            logger.error(f"Error validating symbol uniqueness {symbol}: {str(e)}")
            return False

    # === Statistics and Analytics ===

    async def count_equities(self, **filters) -> int:
        """
        Count equities with optional filters.
        """
        try:
            return await self.db_service.count(**filters)
        except Exception as e:
            logger.error(f"Error counting equities: {str(e)}")
            return 0

    async def get_equity_summary_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive equity statistics for dashboards.
        """
        try:
            # Get counts
            total_equities = await self.count_equities()
            active_equities = await self.count_equities(is_active=True)

            # Get breakdown data (limited set for performance)
            all_active_equities = await self.get_active_equities()

            # Calculate breakdowns
            sector_breakdown = {}
            currency_breakdown = {}

            for equity in all_active_equities:
                sector = equity.sector or "Unknown"
                currency = equity.currency or "Unknown"

                sector_breakdown[sector] = sector_breakdown.get(sector, 0) + 1
                currency_breakdown[currency] = currency_breakdown.get(currency, 0) + 1

            return {
                "total_equities": total_equities,
                "active_equities": active_equities,
                "inactive_equities": total_equities - active_equities,
                "sector_breakdown": sector_breakdown,
                "currency_breakdown": currency_breakdown,
                "last_updated": datetime.datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting equity summary stats: {str(e)}")
            return {
                "total_equities": 0,
                "active_equities": 0,
                "inactive_equities": 0,
                "sector_breakdown": {},
                "currency_breakdown": {},
                "error": str(e),
                "last_updated": datetime.datetime.now().isoformat()
            }

    # === Batch Processing for Performance ===

    async def get_current_prices(self, equity_ids: List[int]) -> Dict[int, float]:
        """
        Get current prices for multiple equities.
        """
        try:
            equities = await self.get_equities_bulk(equity_ids)
            return {equity.id: equity.current_price for equity in equities if equity.current_price}
        except Exception as e:
            logger.error(f"Error getting current prices: {str(e)}")
            return {}

    async def get_equity_essentials(self, equity_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Get essential information for multiple equities.
        """
        try:
            equities = await self.get_equities_bulk(equity_ids)
            return {
                equity.id: {
                    "symbol": equity.symbol,
                    "company_name": equity.company_name,
                    "current_price": equity.current_price,
                    "currency": equity.currency,
                    "sector": equity.sector,
                    "is_active": equity.is_active
                }
                for equity in equities
            }
        except Exception as e:
            logger.error(f"Error getting equity essentials: {str(e)}")
            return {}

    # === Future Cache Management Methods ===

    # async def invalidate_cache(self, equity_id: int):
    #     """Invalidate cache for specific equity"""
    #     await self.cache.delete(f"equity:{equity_id}")

    # async def invalidate_symbol_cache(self, symbol: str):
    #     """Invalidate cache for specific symbol"""
    #     await self.cache.delete(f"equity:symbol:{symbol}")

    # async def warm_cache(self, equity_ids: List[int]):
    #     """Pre-warm cache with frequently accessed equities"""
    #     equities = await self.get_equities_bulk(equity_ids)
    #     for equity in equities:
    #         await self.cache.setex(f"equity:{equity.id}", 3600, equity.json())


# Factory function
def get_equity_read_service() -> EquityReadOnlyService:
    """Factory function for dependency injection"""
    return EquityReadOnlyService()
