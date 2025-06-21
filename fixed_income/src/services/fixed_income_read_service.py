import datetime
import logging
from typing import Any, Dict, List, Optional

from fixed_income.src.database.bond_database_service import BondDatabaseService
from fixed_income.src.model.bonds.BondBase import BondBase
from fixed_income.src.model.enums import BondTypeEnum
from fixed_income.src.utils.model_mappers import bond_model_factory, bond_schema_factory

logger = logging.getLogger(__name__)


class BondReadOnlyService:
    """
    Pure Read-Only Bond Service

    Handles all read operations for different bond types with future caching support.
    No write operations - completely focused on data retrieval and validation.
    Optimized for high-performance lookups and bulk operations.
    """

    def __init__(self):
        self._db_services = {}  # Cache for database services by bond type
        # Future: self.cache = RedisCache() or MemcachedCache()

    def _get_db_service(self, bond_type: BondTypeEnum) -> BondDatabaseService:
        """Get or create database service for specific bond type"""
        if bond_type not in self._db_services:
            model_class = bond_model_factory(bond_type.value)
            schemas = bond_schema_factory(bond_type.value)

            self._db_services[bond_type] = BondDatabaseService(
                bond_base_model=BondBase,
                model=model_class,
                create_schema=schemas['request'],
                response_schema=schemas['response']
            )

        return self._db_services[bond_type]

    # === Core Read Operations ===

    async def get_bond_by_id(self, bond_id: int, bond_type: BondTypeEnum) -> Optional[Any]:
        """
        Get bond by ID with future caching support.
        """
        try:
            # Future: Check cache first
            # cached = await self.cache.get(f"bond:{bond_type.value}:{bond_id}")
            # if cached: return ResponseSchema.parse_raw(cached)

            db_service = self._get_db_service(bond_type)
            bond = await db_service.get_by_id(bond_id)

            # Future: Cache the result
            # if bond: await self.cache.setex(f"bond:{bond_type.value}:{bond_id}", 3600, bond.json())

            return bond
        except Exception as e:
            logger.error(f"Error getting {bond_type.value} bond by ID {bond_id}: {str(e)}")
            return None

    async def get_bond_by_symbol(self, symbol: str, bond_type: BondTypeEnum) -> Optional[Any]:
        """
        Get bond by symbol with future caching support.
        """
        try:
            # Future: Check cache first
            # cached = await self.cache.get(f"bond:symbol:{bond_type.value}:{symbol}")
            # if cached: return ResponseSchema.parse_raw(cached)

            db_service = self._get_db_service(bond_type)
            bonds = await db_service.get_by_column("symbol", symbol)
            bond = bonds[0] if bonds else None

            # Future: Cache the result
            # if bond: await self.cache.setex(f"bond:symbol:{bond_type.value}:{symbol}", 3600, bond.json())

            return bond
        except Exception as e:
            logger.error(f"Error getting {bond_type.value} bond by symbol {symbol}: {str(e)}")
            return None

    async def get_bonds_bulk(self, bond_ids: List[int], bond_type: BondTypeEnum) -> List[Any]:
        """
        Bulk bond retrieval with optimized queries and future caching.
        """
        try:
            # Future: Check cache for each ID first, only query missing ones
            db_service = self._get_db_service(bond_type)
            return await db_service.get_by_ids(bond_ids)
        except Exception as e:
            logger.error(f"Error in bulk {bond_type.value} bond retrieval: {str(e)}")
            return []

    async def get_bonds_by_symbols_bulk(self, symbols: List[str], bond_type: BondTypeEnum) -> List[Any]:
        """
        Optimized bulk bond retrieval by symbols using single query.
        """
        try:
            db_service = self._get_db_service(bond_type)
            return await db_service.get_by_column("symbol", symbols)
        except Exception as e:
            logger.error(f"Error in bulk symbol retrieval for {bond_type.value}: {str(e)}")
            return []

    async def get_all_bonds(
            self,
            bond_type: BondTypeEnum,
            order_by: str = "id",
            desc: bool = False
    ) -> List[Any]:
        """
        Get all bonds of a specific type with ordering.
        """
        try:
            db_service = self._get_db_service(bond_type)
            return await db_service.get_all(order_by=order_by, desc=desc)
        except Exception as e:
            logger.error(f"Error getting all {bond_type.value} bonds: {str(e)}")
            return []

    # === Filtered Read Operations ===

    async def get_active_bonds(self, bond_type: BondTypeEnum) -> List[Any]:
        """
        Get only active bonds of a specific type.
        """
        try:
            # Future: Cache active bond list with shorter TTL
            db_service = self._get_db_service(bond_type)
            return await db_service.get_by_column("is_active", True)
        except Exception as e:
            logger.error(f"Error getting active {bond_type.value} bonds: {str(e)}")
            return []

    async def get_bonds_by_issuer(self, issuer: str, bond_type: BondTypeEnum) -> List[Any]:
        """
        Get bonds by issuer for a specific bond type.
        """
        try:
            db_service = self._get_db_service(bond_type)
            return await db_service.get_by_column("issuer", issuer)
        except Exception as e:
            logger.error(f"Error getting {bond_type.value} bonds by issuer {issuer}: {str(e)}")
            return []

    async def get_bonds_by_currency(self, currency: str, bond_type: BondTypeEnum) -> List[Any]:
        """
        Get bonds by currency for a specific bond type.
        """
        try:
            db_service = self._get_db_service(bond_type)
            return await db_service.get_by_column("currency", currency)
        except Exception as e:
            logger.error(f"Error getting {bond_type.value} bonds by currency {currency}: {str(e)}")
            return []

    async def get_bonds_by_maturity_range(
            self,
            start_date: datetime.date,
            end_date: datetime.date,
            bond_type: BondTypeEnum
    ) -> List[Any]:
        """
        Get bonds maturing within a date range for a specific bond type.
        """
        try:
            db_service = self._get_db_service(bond_type)
            # This would need custom query implementation in database service
            query = f"""
                SELECT * FROM {bond_type.value.lower()}_bonds 
                WHERE maturity_date BETWEEN :start_date AND :end_date
            """
            results = await db_service.execute_raw_query(
                query,
                {"start_date": start_date, "end_date": end_date}
            )
            # Convert raw results to response schemas - would need additional logic
            return results
        except Exception as e:
            logger.error(f"Error getting {bond_type.value} bonds by maturity range: {str(e)}")
            return []

    # === Search Operations ===

    async def search_bonds(self, search_term: str, bond_type: BondTypeEnum) -> List[Any]:
        """
        Search bonds across multiple columns for a specific bond type.
        """
        try:
            search_columns = ["symbol", "issuer", "description"]
            db_service = self._get_db_service(bond_type)
            return await db_service.search(search_term, search_columns)
        except Exception as e:
            logger.error(f"Error searching {bond_type.value} bonds with term '{search_term}': {str(e)}")
            return []

    # === Validation Operations ===

    async def validate_bond_exists(self, bond_id: int, bond_type: BondTypeEnum) -> bool:
        """
        Validate that a bond exists by ID for a specific bond type.
        """
        try:
            # Future: Check cache first for faster validation
            db_service = self._get_db_service(bond_type)
            return await db_service.exists(bond_id)
        except Exception as e:
            logger.error(f"Error validating {bond_type.value} bond {bond_id}: {str(e)}")
            return False

    async def validate_bonds_exist(self, bond_ids: List[int], bond_type: BondTypeEnum) -> Dict[int, bool]:
        """
        Validate multiple bonds exist for a specific bond type.
        """
        try:
            results = {}
            for bond_id in bond_ids:
                results[bond_id] = await self.validate_bond_exists(bond_id, bond_type)
            return results
        except Exception as e:
            logger.error(f"Error validating {bond_type.value} bonds exist: {str(e)}")
            return {bond_id: False for bond_id in bond_ids}

    async def validate_symbol_unique(self, symbol: str, bond_type: BondTypeEnum, exclude_id: int = None) -> bool:
        """
        Validate that a symbol is unique for a specific bond type.

        Args:
            symbol: Symbol to check
            bond_type: Type of bond
            exclude_id: Optional bond ID to exclude from check (for updates)

        Returns:
            True if symbol is unique, False if duplicate exists
        """
        try:
            existing_bond = await self.get_bond_by_symbol(symbol, bond_type)
            if not existing_bond:
                return True

            # If exclude_id provided, check if found bond is the same one being updated
            if exclude_id and existing_bond.id == exclude_id:
                return True

            return False
        except Exception as e:
            logger.error(f"Error validating symbol uniqueness {symbol} for {bond_type.value}: {str(e)}")
            return False

    # === Statistics and Analytics ===

    async def count_bonds(self, bond_type: BondTypeEnum, **filters) -> int:
        """
        Count bonds with optional filters for a specific bond type.
        """
        try:
            db_service = self._get_db_service(bond_type)
            return await db_service.count(**filters)
        except Exception as e:
            logger.error(f"Error counting {bond_type.value} bonds: {str(e)}")
            return 0

    async def get_bond_summary_stats(self, bond_type: BondTypeEnum) -> Dict[str, Any]:
        """
        Get comprehensive bond statistics for dashboards for a specific bond type.
        """
        try:
            # Get counts
            total_bonds = await self.count_bonds(bond_type)
            active_bonds = await self.count_bonds(bond_type, is_active=True)

            # Get breakdown data (limited set for performance)
            all_active_bonds = await self.get_active_bonds(bond_type)

            # Calculate breakdowns
            issuer_breakdown = {}
            currency_breakdown = {}

            for bond in all_active_bonds:
                issuer = bond.issuer or "Unknown"
                currency = bond.currency or "Unknown"

                issuer_breakdown[issuer] = issuer_breakdown.get(issuer, 0) + 1
                currency_breakdown[currency] = currency_breakdown.get(currency, 0) + 1

            return {
                "bond_type": bond_type.value,
                "total_bonds": total_bonds,
                "active_bonds": active_bonds,
                "inactive_bonds": total_bonds - active_bonds,
                "issuer_breakdown": issuer_breakdown,
                "currency_breakdown": currency_breakdown,
                "last_updated": datetime.datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting {bond_type.value} bond summary stats: {str(e)}")
            return {
                "bond_type": bond_type.value,
                "total_bonds": 0,
                "active_bonds": 0,
                "inactive_bonds": 0,
                "issuer_breakdown": {},
                "currency_breakdown": {},
                "error": str(e),
                "last_updated": datetime.datetime.now().isoformat()
            }

    async def get_all_bond_types_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all bond types.
        """
        bond_types = list(BondTypeEnum)
        summary = {}

        for bond_type in bond_types:
            try:
                summary[bond_type.value] = await self.get_bond_summary_stats(bond_type)
            except Exception as e:
                logger.error(f"Error getting summary for {bond_type.value}: {str(e)}")
                summary[bond_type.value] = {"error": str(e)}

        return summary

    # === Batch Processing for Performance ===

    async def get_current_prices(self, bond_ids: List[int], bond_type: BondTypeEnum) -> Dict[int, float]:
        """
        Get current prices for multiple bonds of a specific type.
        """
        try:
            bonds = await self.get_bonds_bulk(bond_ids, bond_type)
            return {bond.id: bond.current_price for bond in bonds if
                    hasattr(bond, 'current_price') and bond.current_price}
        except Exception as e:
            logger.error(f"Error getting current prices for {bond_type.value}: {str(e)}")
            return {}

    async def get_bond_essentials(self, bond_ids: List[int], bond_type: BondTypeEnum) -> Dict[int, Dict[str, Any]]:
        """
        Get essential information for multiple bonds of a specific type.
        """
        try:
            bonds = await self.get_bonds_bulk(bond_ids, bond_type)
            return {
                bond.id: {
                    "symbol": bond.symbol,
                    "issuer": bond.issuer,
                    "current_price": getattr(bond, 'current_price', None),
                    "currency": bond.currency,
                    "maturity_date": bond.maturity_date,
                    "is_active": bond.is_active,
                    "bond_type": bond_type.value
                }
                for bond in bonds
            }
        except Exception as e:
            logger.error(f"Error getting {bond_type.value} bond essentials: {str(e)}")
            return {}

    # === Future Cache Management Methods ===

    # async def invalidate_cache(self, bond_id: int, bond_type: BondTypeEnum):
    #     """Invalidate cache for specific bond"""
    #     await self.cache.delete(f"bond:{bond_type.value}:{bond_id}")

    # async def invalidate_symbol_cache(self, symbol: str, bond_type: BondTypeEnum):
    #     """Invalidate cache for specific symbol"""
    #     await self.cache.delete(f"bond:symbol:{bond_type.value}:{symbol}")

    # async def warm_cache(self, bond_ids: List[int], bond_type: BondTypeEnum):
    #     """Pre-warm cache with frequently accessed bonds"""
    #     bonds = await self.get_bonds_bulk(bond_ids, bond_type)
    #     for bond in bonds:
    #         await self.cache.setex(f"bond:{bond_type.value}:{bond.id}", 3600, bond.json())


# Factory function
def get_bond_read_service() -> BondReadOnlyService:
    """Factory function for dependency injection"""
    return BondReadOnlyService()
