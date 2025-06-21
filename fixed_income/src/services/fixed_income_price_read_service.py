import datetime
import logging
from typing import Any, Dict, List, Optional

from fixed_income.src.api.bond_schema.BondPriceSchema import BondPriceRequest, BondPriceResponse
from fixed_income.src.model.bonds.BondPrice import BondPrice  # Assuming this model exists

from fixed_income.src.database.generic_database_service import GenericDatabaseService
from fixed_income.src.services.fixed_income_read_service import get_bond_read_service

logger = logging.getLogger(__name__)


class BondPriceReadOnlyService:
    """
    Pure Read-Only Bond Price Service

    Handles all price-related read operations with future caching support.
    Optimized for high-frequency price lookups and historical data retrieval.
    Supports multiple bond types and pricing methodologies.
    """

    def __init__(self):
        self.db_service = GenericDatabaseService(
            model=BondPrice,
            create_schema=BondPriceRequest,
            response_schema=BondPriceResponse
        )
        self.bond_read_service = get_bond_read_service()
        # Future: self.price_cache = RedisPriceCache()

    # === Current Price Operations ===

    async def get_current_price(self, bond_id: int, bond_type: str) -> Optional[BondPriceResponse]:
        """
        Get the most recent price for a single bond.
        """
        try:
            # Future: Check cache first
            # cached = await self.price_cache.get(f"current_price:{bond_type}:{bond_id}")
            # if cached: return BondPriceResponse.parse_raw(cached)

            # Get latest price from database
            prices = await self.db_service.get_by_column(
                column_name="bond_id",
                value=bond_id
            )

            # Filter by bond_type and get most recent
            bond_type_prices = [p for p in prices if p.bond_type == bond_type]
            if bond_type_prices:
                # Sort by timestamp to get most recent
                current_price = max(bond_type_prices, key=lambda x: x.timestamp)
            else:
                current_price = None

            # Future: Cache the result with short TTL
            # if current_price:
            #     await self.price_cache.setex(f"current_price:{bond_type}:{bond_id}", 30, current_price.json())

            return current_price
        except Exception as e:
            logger.error(f"Error getting current price for {bond_type} bond {bond_id}: {str(e)}")
            return None

    async def get_current_prices_bulk(self, bond_ids: List[int], bond_type: str) -> Dict[int, BondPriceResponse]:
        """
        Get current prices for multiple bonds efficiently.
        """
        try:
            # Future: Batch cache lookup
            current_prices = {}

            for bond_id in bond_ids:
                price = await self.get_current_price(bond_id, bond_type)
                if price:
                    current_prices[bond_id] = price

            return current_prices
        except Exception as e:
            logger.error(f"Error in bulk current price retrieval for {bond_type}: {str(e)}")
            return {}

    async def get_current_prices_by_symbols(self, symbols: List[str], bond_type: str) -> Dict[str, BondPriceResponse]:
        """
        Get current prices by bond symbols.
        """
        try:
            # First get bond IDs for symbols
            bonds = await self.bond_read_service.get_bonds_by_symbols_bulk(symbols, bond_type)
            symbol_to_bond = {bond.symbol: bond for bond in bonds}

            result = {}
            for symbol in symbols:
                if symbol in symbol_to_bond:
                    bond = symbol_to_bond[symbol]
                    price = await self.get_current_price(bond.id, bond_type)
                    if price:
                        result[symbol] = price

            return result
        except Exception as e:
            logger.error(f"Error getting current prices by symbols for {bond_type}: {str(e)}")
            return {}

    # === Historical Price Operations ===

    async def get_price_history(
            self,
            bond_id: int,
            bond_type: str,
            start_date: datetime.datetime = None,
            end_date: datetime.datetime = None,
            limit: int = 100
    ) -> List[BondPriceResponse]:
        """
        Get historical prices for a bond within date range.
        """
        try:
            # Get all prices for the bond
            all_prices = await self.db_service.get_by_column("bond_id", bond_id)

            # Filter by bond type and date range
            filtered_prices = []
            for price in all_prices:
                if price.bond_type != bond_type:
                    continue

                if start_date and price.timestamp < start_date:
                    continue

                if end_date and price.timestamp > end_date:
                    continue

                filtered_prices.append(price)

            # Sort by timestamp (most recent first) and apply limit
            filtered_prices.sort(key=lambda x: x.timestamp, reverse=True)
            return filtered_prices[:limit]

        except Exception as e:
            logger.error(f"Error getting price history for {bond_type} bond {bond_id}: {str(e)}")
            return []

    async def get_price_at_date(
            self,
            bond_id: int,
            bond_type: str,
            target_date: datetime.datetime
    ) -> Optional[BondPriceResponse]:
        """
        Get price closest to a specific date (on or before).
        """
        try:
            # Get price history up to target date
            prices = await self.get_price_history(
                bond_id=bond_id,
                bond_type=bond_type,
                end_date=target_date,
                limit=1
            )

            return prices[0] if prices else None
        except Exception as e:
            logger.error(f"Error getting price at date for {bond_type} bond {bond_id}: {str(e)}")
            return None

    async def get_price_range(
            self,
            bond_id: int,
            bond_type: str,
            days: int = 30
    ) -> Dict[str, Any]:
        """
        Get high, low, and other statistics for recent price range.
        """
        try:
            start_date = datetime.datetime.now() - datetime.timedelta(days=days)
            prices = await self.get_price_history(
                bond_id=bond_id,
                bond_type=bond_type,
                start_date=start_date,
                limit=1000  # Sufficient for most ranges
            )

            if not prices:
                return {}

            price_values = [float(price.price) for price in prices]

            return {
                "bond_id": bond_id,
                "bond_type": bond_type,
                "period_days": days,
                "high": max(price_values),
                "low": min(price_values),
                "current": price_values[0],  # Most recent (first in desc order)
                "average": sum(price_values) / len(price_values),
                "data_points": len(price_values),
                "start_date": start_date.isoformat(),
                "end_date": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error calculating price range for {bond_type} bond {bond_id}: {str(e)}")
            return {}

    async def get_price_performance(
            self,
            bond_id: int,
            bond_type: str,
            periods: List[int]
    ) -> Dict[str, Any]:
        """
        Calculate price performance over multiple periods.
        """
        try:
            current_price = await self.get_current_price(bond_id, bond_type)
            if not current_price:
                return {}

            performance = {
                "bond_id": bond_id,
                "bond_type": bond_type,
                "current_price": float(current_price.price),
                "currency": current_price.currency,
                "periods": {}
            }

            for days in periods:
                past_date = datetime.datetime.now() - datetime.timedelta(days=days)
                past_price = await self.get_price_at_date(bond_id, bond_type, past_date)

                if past_price:
                    change = float(current_price.price) - float(past_price.price)
                    change_percent = (change / float(past_price.price)) * 100

                    performance["periods"][f"{days}d"] = {
                        "past_price": float(past_price.price),
                        "change": change,
                        "change_percent": round(change_percent, 2),
                        "past_date": past_price.timestamp.isoformat()
                    }

            return performance
        except Exception as e:
            logger.error(f"Error calculating price performance for {bond_type} bond {bond_id}: {str(e)}")
            return {}

    async def compare_bond_prices(
            self,
            bond_ids: List[int],
            bond_type: str,
            start_date: datetime.datetime = None
    ) -> Dict[str, Any]:
        """
        Compare price performance across multiple bonds of the same type.
        """
        try:
            if not start_date:
                start_date = datetime.datetime.now() - datetime.timedelta(days=30)

            comparison_data = {}

            for bond_id in bond_ids:
                bond = await self.bond_read_service.get_bond_by_id(bond_id, bond_type)
                if not bond:
                    continue

                current_price = await self.get_current_price(bond_id, bond_type)
                start_price = await self.get_price_at_date(bond_id, bond_type, start_date)

                if current_price and start_price:
                    change = float(current_price.price) - float(start_price.price)
                    change_percent = (change / float(start_price.price)) * 100

                    comparison_data[bond_id] = {
                        "symbol": bond.symbol,
                        "issuer": bond.issuer,
                        "start_price": float(start_price.price),
                        "current_price": float(current_price.price),
                        "change": change,
                        "change_percent": round(change_percent, 2),
                        "currency": current_price.currency,
                    }

            return {
                "bond_type": bond_type,
                "comparison_date": start_date.isoformat(),
                "current_date": datetime.datetime.now().isoformat(),
                "bonds": comparison_data
            }
        except Exception as e:
            logger.error(f"Error comparing {bond_type} bond prices: {str(e)}")
            return {}

    # === Market Data Validation ===

    async def validate_price_data_quality(
            self,
            bond_id: int,
            bond_type: str,
            days: int = 7
    ) -> Dict[str, Any]:
        """
        Analyze price data quality and identify gaps or anomalies.
        """
        try:
            start_date = datetime.datetime.now() - datetime.timedelta(days=days)
            prices = await self.get_price_history(
                bond_id=bond_id,
                bond_type=bond_type,
                start_date=start_date
            )

            if not prices:
                return {"status": "no_data", "bond_id": bond_id, "bond_type": bond_type}

            # Analyze data quality
            price_values = [float(price.price) for price in prices]
            timestamps = [price.timestamp for price in prices]

            # Check for gaps
            gaps = []
            for i in range(1, len(timestamps)):
                time_diff = timestamps[i - 1] - timestamps[i]  # Desc order
                if time_diff.total_seconds() > 86400:  # More than 1 day gap
                    gaps.append({
                        "start": timestamps[i].isoformat(),
                        "end": timestamps[i - 1].isoformat(),
                        "duration_hours": time_diff.total_seconds() / 3600
                    })

            # Check for anomalies (more conservative for bonds)
            anomalies = []
            if len(price_values) > 2:
                avg_price = sum(price_values) / len(price_values)
                for i, price in enumerate(price_values):
                    deviation = abs(price - avg_price) / avg_price
                    if deviation > 0.05:  # 5% deviation threshold for bonds
                        anomalies.append({
                            "timestamp": timestamps[i].isoformat(),
                            "price": price,
                            "deviation_percent": round(deviation * 100, 2)
                        })

            return {
                "bond_id": bond_id,
                "bond_type": bond_type,
                "period_days": days,
                "total_data_points": len(prices),
                "data_gaps": gaps,
                "price_anomalies": anomalies,
                "analysis_date": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error validating price data quality for {bond_type} bond {bond_id}: {str(e)}")
            return {"status": "error", "bond_id": bond_id, "bond_type": bond_type, "error": str(e)}

    # === Statistics and Aggregations ===

    async def get_bond_market_summary(
            self,
            bond_type: str,
            bond_ids: List[int] = None,
            issuer: str = None
    ) -> Dict[str, Any]:
        """
        Get bond market summary statistics for a specific bond type.
        """
        try:
            if not bond_ids:
                if issuer:
                    bonds = await self.bond_read_service.get_bonds_by_issuer(issuer, bond_type)
                else:
                    bonds = await self.bond_read_service.get_active_bonds(bond_type)
                bond_ids = [bond.id for bond in bonds]

            current_prices = await self.get_current_prices_bulk(bond_ids, bond_type)

            if not current_prices:
                return {}

            price_values = [float(price.price) for price in current_prices.values()]

            # Calculate performance for 1 day
            performance_data = []
            yield_data = []

            for bond_id in bond_ids:
                perf = await self.get_price_performance(bond_id, bond_type, [1])
                if perf.get("periods", {}).get("1d"):
                    performance_data.append(perf["periods"]["1d"]["change_percent"])

            gainers = len([p for p in performance_data if p > 0])
            losers = len([p for p in performance_data if p < 0])
            unchanged = len(performance_data) - gainers - losers

            return {
                "bond_type": bond_type,
                "total_bonds": len(bond_ids),
                "prices_available": len(current_prices),
                "issuer": issuer,
                "market_stats": {
                    "gainers": gainers,
                    "losers": losers,
                    "unchanged": unchanged,
                    "avg_change_percent": round(sum(performance_data) / len(performance_data),
                                                2) if performance_data else 0
                },
                "price_stats": {
                    "highest_price": max(price_values),
                    "lowest_price": min(price_values),
                    "average_price": round(sum(price_values) / len(price_values), 2)
                },
                "yield_stats": {
                    "average_yield": round(sum(yield_data) / len(yield_data), 2) if yield_data else 0,
                    "highest_yield": max(yield_data) if yield_data else 0,
                    "lowest_yield": min(yield_data) if yield_data else 0
                },
                "generated_at": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating {bond_type} bond market summary: {str(e)}")
            return {}

    # === Future Cache Management ===

    # async def invalidate_price_cache(self, bond_id: int, bond_type: str):
    #     """Invalidate price cache for specific bond"""
    #     await self.price_cache.delete(f"current_price:{bond_type}:{bond_id}")
    #     await self.price_cache.delete_pattern(f"price_history:{bond_type}:{bond_id}:*")

    # async def warm_price_cache(self, bond_ids: List[int], bond_type: str):
    #     """Pre-warm cache with current prices"""
    #     current_prices = await self.get_current_prices_bulk(bond_ids, bond_type)
    #     for bond_id, price in current_prices.items():
    #         await self.price_cache.setex(f"current_price:{bond_type}:{bond_id}", 30, price.json())


# Factory function
def get_bond_price_read_service() -> BondPriceReadOnlyService:
    """Factory function for dependency injection"""
    return BondPriceReadOnlyService()
