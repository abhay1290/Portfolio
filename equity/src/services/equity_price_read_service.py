import datetime
import logging
from typing import Any, Dict, List, Optional

from equity.src.model.equity.EquityPrice import EquityPrice  # Assuming this model exists

from equity.src.api.equity_schema.Equity_Schema import EquityPriceRequest, EquityPriceResponse
from equity.src.database.equity_database_service import EquityDatabaseService
from equity.src.services.equity_read_service import get_equity_read_service

logger = logging.getLogger(__name__)


class EquityPriceReadOnlyService:
    """
    Pure Read-Only Equity Price Service

    Handles all price-related read operations with future caching support.
    Optimized for high-frequency price lookups and historical data retrieval.
    """

    def __init__(self):
        self.db_service = EquityDatabaseService(
            model=EquityPrice,
            create_schema=EquityPriceRequest,
            response_schema=EquityPriceResponse
        )
        self.equity_read_service = get_equity_read_service()
        # Future: self.price_cache = RedisPriceCache()

    # === Current Price Operations ===

    async def get_current_price(self, equity_id: int) -> Optional[EquityPriceResponse]:
        """
        Get the most recent price for a single equity.
        """
        try:
            # Future: Check cache first
            # cached = await self.price_cache.get(f"current_price:{equity_id}")
            # if cached: return EquityPriceResponse.parse_raw(cached)

            # Get latest price from database
            prices = await self.db_service.get_by_column(
                column="equity_id",
                value=equity_id,
                order_by="timestamp",
                desc=True,
                limit=1
            )

            current_price = prices[0] if prices else None

            # Future: Cache the result with short TTL
            # if current_price:
            #     await self.price_cache.setex(f"current_price:{equity_id}", 30, current_price.json())

            return current_price
        except Exception as e:
            logger.error(f"Error getting current price for equity {equity_id}: {str(e)}")
            return None

    async def get_current_prices_bulk(self, equity_ids: List[int]) -> Dict[int, EquityPriceResponse]:
        """
        Get current prices for multiple equities efficiently.
        """
        try:
            # Future: Batch cache lookup
            current_prices = {}

            for equity_id in equity_ids:
                price = await self.get_current_price(equity_id)
                if price:
                    current_prices[equity_id] = price

            return current_prices
        except Exception as e:
            logger.error(f"Error in bulk current price retrieval: {str(e)}")
            return {}

    async def get_current_prices_by_symbols(self, symbols: List[str]) -> Dict[str, EquityPriceResponse]:
        """
        Get current prices by equity symbols.
        """
        try:
            # First get equity IDs for symbols
            equities = await self.equity_read_service.get_equities_by_symbols_bulk(symbols)
            symbol_to_equity = {equity.symbol: equity for equity in equities}

            result = {}
            for symbol in symbols:
                if symbol in symbol_to_equity:
                    equity = symbol_to_equity[symbol]
                    price = await self.get_current_price(equity.id)
                    if price:
                        result[symbol] = price

            return result
        except Exception as e:
            logger.error(f"Error getting current prices by symbols: {str(e)}")
            return {}

    # === Historical Price Operations ===

    async def get_price_history(
            self,
            equity_id: int,
            start_date: datetime.datetime = None,
            end_date: datetime.datetime = None,
            limit: int = 100
    ) -> List[EquityPriceResponse]:
        """
        Get historical prices for an equity within date range.
        """
        try:
            filters = {"equity_id": equity_id}

            if start_date:
                filters["timestamp__gte"] = start_date
            if end_date:
                filters["timestamp__lte"] = end_date

            return await self.db_service.get_filtered(
                filters=filters,
                order_by="timestamp",
                desc=True,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting price history for equity {equity_id}: {str(e)}")
            return []

    async def get_price_at_date(
            self,
            equity_id: int,
            target_date: datetime.datetime
    ) -> Optional[EquityPriceResponse]:
        """
        Get price closest to a specific date (on or before).
        """
        try:
            prices = await self.db_service.get_filtered(
                filters={
                    "equity_id": equity_id,
                    "timestamp__lte": target_date
                },
                order_by="timestamp",
                desc=True,
                limit=1
            )

            return prices[0] if prices else None
        except Exception as e:
            logger.error(f"Error getting price at date for equity {equity_id}: {str(e)}")
            return None

    async def get_price_range(
            self,
            equity_id: int,
            days: int = 30
    ) -> Dict[str, Any]:
        """
        Get high, low, and other statistics for recent price range.
        """
        try:
            start_date = datetime.datetime.now() - datetime.timedelta(days=days)
            prices = await self.get_price_history(
                equity_id=equity_id,
                start_date=start_date,
                limit=1000  # Sufficient for most ranges
            )

            if not prices:
                return {}

            price_values = [float(price.price) for price in prices]

            return {
                "equity_id": equity_id,
                "period_days": days,
                "high": max(price_values),
                "low": min(price_values),
                "current": price_values[0],  # Most recent (first in desc order)
                "average": sum(price_values) / len(price_values),
                "volatility": self._calculate_volatility(price_values),
                "data_points": len(price_values),
                "start_date": start_date.isoformat(),
                "end_date": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error calculating price range for equity {equity_id}: {str(e)}")
            return {}

    # === Price Analytics ===

    async def get_price_performance(
            self,
            equity_id: int,
            periods: List[int]
    ) -> Dict[str, Any]:
        """
        Calculate price performance over multiple periods.
        """
        try:
            current_price = await self.get_current_price(equity_id)
            if not current_price:
                return {}

            performance = {
                "equity_id": equity_id,
                "current_price": float(current_price.price),
                "currency": current_price.currency,
                "periods": {}
            }

            for days in periods:
                past_date = datetime.datetime.now() - datetime.timedelta(days=days)
                past_price = await self.get_price_at_date(equity_id, past_date)

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
            logger.error(f"Error calculating price performance for equity {equity_id}: {str(e)}")
            return {}

    async def compare_prices(
            self,
            equity_ids: List[int],
            start_date: datetime.datetime = None
    ) -> Dict[str, Any]:
        """
        Compare price performance across multiple equities.
        """
        try:
            if not start_date:
                start_date = datetime.datetime.now() - datetime.timedelta(days=30)

            comparison_data = {}

            for equity_id in equity_ids:
                equity = await self.equity_read_service.get_equity_by_id(equity_id)
                if not equity:
                    continue

                current_price = await self.get_current_price(equity_id)
                start_price = await self.get_price_at_date(equity_id, start_date)

                if current_price and start_price:
                    change = float(current_price.price) - float(start_price.price)
                    change_percent = (change / float(start_price.price)) * 100

                    comparison_data[equity_id] = {
                        "symbol": equity.symbol,
                        "company_name": equity.company_name,
                        "start_price": float(start_price.price),
                        "current_price": float(current_price.price),
                        "change": change,
                        "change_percent": round(change_percent, 2),
                        "currency": current_price.currency
                    }

            return {
                "comparison_date": start_date.isoformat(),
                "current_date": datetime.datetime.now().isoformat(),
                "equities": comparison_data
            }
        except Exception as e:
            logger.error(f"Error comparing prices: {str(e)}")
            return {}

    # === Market Data Validation ===

    async def validate_price_data_quality(
            self,
            equity_id: int,
            days: int = 7
    ) -> Dict[str, Any]:
        """
        Analyze price data quality and identify gaps or anomalies.
        """
        try:
            start_date = datetime.datetime.now() - datetime.timedelta(days=days)
            prices = await self.get_price_history(
                equity_id=equity_id,
                start_date=start_date,
                limit=1000
            )

            if not prices:
                return {"status": "no_data", "equity_id": equity_id}

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

            # Check for anomalies
            anomalies = []
            if len(price_values) > 2:
                avg_price = sum(price_values) / len(price_values)
                for i, price in enumerate(price_values):
                    deviation = abs(price - avg_price) / avg_price
                    if deviation > 0.2:  # 20% deviation threshold
                        anomalies.append({
                            "timestamp": timestamps[i].isoformat(),
                            "price": price,
                            "deviation_percent": round(deviation * 100, 2)
                        })

            return {
                "equity_id": equity_id,
                "period_days": days,
                "total_data_points": len(prices),
                "data_gaps": gaps,
                "price_anomalies": anomalies,
                "data_quality_score": self._calculate_quality_score(gaps, anomalies, len(prices)),
                "analysis_date": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error validating price data quality for equity {equity_id}: {str(e)}")
            return {"status": "error", "equity_id": equity_id, "error": str(e)}

    # === Statistics and Aggregations ===

    async def get_market_summary(
            self,
            equity_ids: List[int] = None,
            sector: str = None
    ) -> Dict[str, Any]:
        """
        Get market summary statistics across equities.
        """
        try:
            if not equity_ids:
                if sector:
                    equities = await self.equity_read_service.get_equities_by_sector(sector)
                else:
                    equities = await self.equity_read_service.get_active_equities()
                equity_ids = [equity.id for equity in equities]

            current_prices = await self.get_current_prices_bulk(equity_ids)

            if not current_prices:
                return {}

            price_values = [float(price.price) for price in current_prices.values()]

            # Calculate performance for 1 day
            performance_data = []
            for equity_id in equity_ids:
                perf = await self.get_price_performance(equity_id, [1])
                if perf.get("periods", {}).get("1d"):
                    performance_data.append(perf["periods"]["1d"]["change_percent"])

            gainers = len([p for p in performance_data if p > 0])
            losers = len([p for p in performance_data if p < 0])
            unchanged = len(performance_data) - gainers - losers

            return {
                "total_equities": len(equity_ids),
                "prices_available": len(current_prices),
                "sector": sector,
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
                "generated_at": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating market summary: {str(e)}")
            return {}

    # === Helper Methods ===

    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate simple volatility (standard deviation)."""
        if len(prices) < 2:
            return 0.0

        mean = sum(prices) / len(prices)
        variance = sum((price - mean) ** 2 for price in prices) / len(prices)
        return round((variance ** 0.5), 4)

    def _calculate_quality_score(self, gaps: List, anomalies: List, total_points: int) -> float:
        """Calculate data quality score (0-100)."""
        if total_points == 0:
            return 0.0

        gap_penalty = min(len(gaps) * 10, 30)  # Max 30 points for gaps
        anomaly_penalty = min(len(anomalies) * 5, 20)  # Max 20 points for anomalies

        score = 100 - gap_penalty - anomaly_penalty
        return max(score, 0.0)

    # === Future Cache Management ===

    # async def invalidate_price_cache(self, equity_id: int):
    #     """Invalidate price cache for specific equity"""
    #     await self.price_cache.delete(f"current_price:{equity_id}")
    #     await self.price_cache.delete_pattern(f"price_history:{equity_id}:*")

    # async def warm_price_cache(self, equity_ids: List[int]):
    #     """Pre-warm cache with current prices"""
    #     current_prices = await self.get_current_prices_bulk(equity_ids)
    #     for equity_id, price in current_prices.items():
    #         await self.price_cache.setex(f"current_price:{equity_id}", 30, price.json())


# Factory function
def get_equity_price_read_service() -> EquityPriceReadOnlyService:
    """Factory function for dependency injection"""
    return EquityPriceReadOnlyService()
