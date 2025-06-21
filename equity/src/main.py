import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Body, Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer

from equity.src.api.equity_schema.Equity_Schema import (
    EquityPriceRequest,
    EquityPriceResponse,
    EquityRequest,
    EquityResponse
)
from equity.src.controller.equity_controller import EquityController, get_equity_controller

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Create the equity router
equity_router = FastAPI(
    title="Equity Service with Controller",
    version="1.1.0",
    description="Microservice for equity and price management with controller layer",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)


# === Core Equity CRUD Operations ===

@equity_router.post("", response_model=EquityResponse, status_code=status.HTTP_201_CREATED)
async def create_equity(
        request: EquityRequest,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Create a new equity instrument."""
    return await controller.create_equity(
        equity_data=request,
        user_token=token
    )


@equity_router.get("/{equity_id}", response_model=EquityResponse)
async def get_equity(
        equity_id: int,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Get a single equity instrument by ID."""
    equity = await controller.get_equity_by_id(equity_id)
    if not equity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equity {equity_id} not found"
        )
    return equity


@equity_router.get("/symbol/{symbol}", response_model=EquityResponse)
async def get_equity_by_symbol(
        symbol: str,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Get equity instrument by symbol."""
    equity = await controller.get_equity_by_symbol(symbol)
    if not equity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equity with symbol {symbol} not found"
        )
    return equity


@equity_router.put("/{equity_id}", response_model=EquityResponse)
async def update_equity(
        equity_id: int,
        request: EquityRequest,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Update an existing equity instrument."""
    return await controller.update_equity(
        equity_id=equity_id,
        equity_data=request,
        user_token=token
    )


@equity_router.patch("/{equity_id}", response_model=EquityResponse)
async def partial_update_equity(
        equity_id: int,
        request: EquityRequest,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Partially update an existing equity instrument."""
    return await controller.partial_update_equity(
        equity_id=equity_id,
        equity_data=request,
        user_token=token
    )


@equity_router.delete("/{equity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equity(
        equity_id: int,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Delete an equity instrument."""
    success = await controller.delete_equity(
        equity_id=equity_id,
        user_token=token
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equity {equity_id} not found"
        )


# === Equity Bulk Operations ===

@equity_router.post("/bulk/create", response_model=List[EquityResponse])
async def bulk_create_equities(
        bulk_request: List[EquityRequest],
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Create multiple equity instruments in bulk."""
    return await controller.bulk_create_equities(
        bulk_request=bulk_request,
        user_token=token
    )


@equity_router.post("/bulk/get", response_model=List[EquityResponse])
async def bulk_get_equities(
        equity_ids: List[int] = Body(..., description="List of equity IDs"),
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Get multiple equity instruments by IDs."""
    return await controller.get_equities_bulk(equity_ids)


@equity_router.post("/bulk/get-by-symbols", response_model=List[EquityResponse])
async def bulk_get_equities_by_symbols(
        symbols: List[str] = Body(..., description="List of equity symbols"),
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Get multiple equity instruments by symbols."""
    return await controller.get_equities_by_symbols_bulk(symbols)


@equity_router.put("/bulk/update", response_model=List[EquityResponse])
async def bulk_update_equities(
        updates: List[Tuple[int, EquityRequest]] = Body(..., description="List of equity updates"),
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Update multiple equity instruments in bulk."""
    return await controller.bulk_update_equities(
        updates=updates,
        user_token=token
    )


# === Equity Listing and Search ===

@equity_router.get("", response_model=List[EquityResponse])
async def get_equities(
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme),
        sector: Optional[str] = Query(None, description="Filter by sector"),
        currency: Optional[str] = Query(None, description="Filter by currency"),
        active_only: bool = Query(False, description="Get only active equities"),
        order_by: str = Query("id", description="Order by field"),
        desc: bool = Query(False, description="Descending order")
):
    """Get list of equity instruments with optional filtering."""
    if sector:
        return await controller.get_equities_by_sector(sector)
    elif currency:
        # Note: You'll need to convert string to CurrencyEnum
        return await controller.get_equities_by_currency(currency)
    elif active_only:
        return await controller.get_active_equities()
    else:
        return await controller.get_all_equities(order_by, desc)


@equity_router.get("/search/{search_term}", response_model=List[EquityResponse])
async def search_equities(
        search_term: str,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Search equity instruments across multiple fields."""
    return await controller.search_equities(search_term)


# === Equity Validation ===

@equity_router.post("/validate/exists", response_model=Dict[int, bool])
async def validate_equities_exist(
        equity_ids: List[int] = Body(..., description="List of equity IDs to validate"),
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Validate that multiple equities exist."""
    return await controller.validate_equities_exist(equity_ids)


@equity_router.get("/validate/{equity_id}/exists")
async def validate_equity_exists(
        equity_id: int,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Validate that a single equity exists."""
    exists = await controller.validate_equity_exists(equity_id)
    return {
        "equity_id": equity_id,
        "exists": exists,
        "validated_at": datetime.now().isoformat()
    }


# === Equity Status Management ===

@equity_router.post("/{equity_id}/activate", response_model=EquityResponse)
async def activate_equity(
        equity_id: int,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Activate an equity instrument."""
    return await controller.activate_equity(equity_id, token)


@equity_router.post("/{equity_id}/deactivate", response_model=EquityResponse)
async def deactivate_equity(
        equity_id: int,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Deactivate an equity instrument."""
    return await controller.deactivate_equity(equity_id, token)


# === Price Operations ===

@equity_router.get("/{equity_id}/price/current", response_model=EquityPriceResponse)
async def get_current_price(
        equity_id: int,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Get current price for a specific equity."""
    price = await controller.get_current_price(equity_id)
    if not price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No current price available for equity {equity_id}"
        )
    return price


@equity_router.post("/prices/current", response_model=Dict[int, EquityPriceResponse])
async def get_current_prices_bulk(
        equity_ids: List[int] = Body(..., description="List of equity IDs"),
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Get current prices for multiple equity instruments."""
    return await controller.get_current_prices_bulk(equity_ids)


@equity_router.post("/prices/by-symbols", response_model=Dict[str, EquityPriceResponse])
async def get_current_prices_by_symbols(
        symbols: List[str] = Body(..., description="List of equity symbols"),
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Get current prices by symbols."""
    return await controller.get_current_prices_by_symbols(symbols)


@equity_router.get("/{equity_id}/price/history", response_model=List[EquityPriceResponse])
async def get_price_history(
        equity_id: int,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme),
        start_date: Optional[datetime] = Query(None, description="Start date for history"),
        end_date: Optional[datetime] = Query(None, description="End date for history"),
        limit: int = Query(100, description="Maximum number of records", ge=1, le=1000)
):
    """Get historical price data for an equity."""
    return await controller.get_price_history(equity_id, start_date, end_date, limit)


@equity_router.post("/{equity_id}/price/update", response_model=EquityPriceResponse)
async def update_price(
        equity_id: int,
        price: Decimal = Body(..., description="New price"),
        timestamp: Optional[datetime] = Body(None, description="Price timestamp"),
        source: str = Body("manual", description="Price source"),
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Update price for a specific equity."""
    return await controller.update_price(
        equity_id=equity_id,
        price=price,
        timestamp=timestamp,
        source=source,
        user_token=token
    )


@equity_router.post("/prices/bulk-update", response_model=List[EquityPriceResponse])
async def bulk_update_prices(
        price_updates: List[EquityPriceRequest] = Body(..., description="Bulk price updates"),
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Update prices for multiple equity instruments."""
    return await controller.bulk_update_prices(price_updates, token)


@equity_router.post("/prices/feed-update", response_model=Dict[str, Any])
async def update_prices_from_feed(
        feed_data: Dict[str, Any] = Body(..., description="Market data feed"),
        source: str = Body("market_feed", description="Data source identifier"),
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Process price updates from external market data feed."""
    return await controller.update_prices_from_feed(feed_data, source, token)


# === Analytics ===

@equity_router.get("/{equity_id}/price/performance", response_model=Dict[str, Any])
async def get_price_performance(
        equity_id: int,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme),
        periods: List[int] = Query([1, 7, 30, 90], description="Performance periods in days")
):
    """Get price performance over multiple periods."""
    return await controller.get_price_performance(equity_id, periods)


@equity_router.get("/{equity_id}/price/range", response_model=Dict[str, Any])
async def get_price_range(
        equity_id: int,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme),
        days: int = Query(30, description="Number of days for range analysis", ge=1, le=365)
):
    """Get price range statistics for an equity."""
    return await controller.get_price_range(equity_id, days)


@equity_router.post("/prices/compare", response_model=Dict[str, Any])
async def compare_prices(
        equity_ids: List[int] = Body(..., description="List of equity IDs to compare"),
        start_date: Optional[datetime] = Body(None, description="Comparison start date"),
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Compare price performance across multiple equities."""
    return await controller.compare_prices(equity_ids, start_date)


@equity_router.get("/market/summary", response_model=Dict[str, Any])
async def get_market_summary(
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme),
        sector: Optional[str] = Query(None, description="Filter by sector"),
        equity_ids: Optional[List[int]] = Query(None, description="Specific equity IDs")
):
    """Get market summary statistics."""
    return await controller.get_market_summary(equity_ids, sector)


# === Statistics ===

@equity_router.get("/statistics/summary", response_model=Dict[str, Any])
async def get_equity_summary_stats(
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Get summary statistics for all equities."""
    return await controller.get_equity_summary_stats()


@equity_router.get("/statistics/count")
async def get_equity_count(
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme),
        sector: Optional[str] = Query(None, description="Filter by sector"),
        active_only: bool = Query(False, description="Count only active equities")
):
    """Get equity count with optional filters."""
    filters = {}
    if sector:
        filters["sector"] = sector
    if active_only:
        filters["is_active"] = True

    count = await controller.count_equities(**filters)
    return {
        "count": count,
        "filters": filters,
        "timestamp": datetime.now().isoformat()
    }


# === Data Quality ===

@equity_router.get("/{equity_id}/data-quality", response_model=Dict[str, Any])
async def check_price_data_quality(
        equity_id: int,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme),
        days: int = Query(7, description="Number of days to analyze", ge=1, le=30)
):
    """Analyze price data quality for an equity."""
    return await controller.validate_price_data_quality(equity_id, days)


# === Administrative Operations ===

@equity_router.post("/{equity_id}/price/correct", response_model=EquityPriceResponse)
async def correct_price(
        equity_id: int,
        price_id: int = Body(..., description="ID of price record to correct"),
        corrected_price: Decimal = Body(..., description="Corrected price value"),
        correction_reason: str = Body(..., description="Reason for correction"),
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Correct a specific price record."""
    return await controller.correct_price(
        price_id=price_id,
        corrected_price=corrected_price,
        correction_reason=correction_reason,
        user_token=token
    )


@equity_router.get("/admin/audit/prices", response_model=Dict[str, Any])
async def get_price_audit_trail(
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme),
        equity_id: Optional[int] = Query(None, description="Filter by equity ID"),
        start_date: Optional[datetime] = Query(None, description="Start date for audit"),
        end_date: Optional[datetime] = Query(None, description="End date for audit"),
        source: Optional[str] = Query(None, description="Filter by data source")
):
    """Get price update audit trail."""
    return await controller.get_price_update_audit(equity_id, start_date, end_date, source)


@equity_router.post("/admin/sync-market-data", response_model=Dict[str, Any])
async def sync_market_data(
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme),
        equity_ids: Optional[List[int]] = Body(None, description="Specific equity IDs to sync"),
        symbols: Optional[List[str]] = Body(None, description="Specific symbols to sync"),
        force_update: bool = Body(False, description="Force update even if recently updated")
):
    """Sync equity data with external market data providers."""
    return await controller.sync_with_market_data(equity_ids, symbols, force_update, token)


@equity_router.post("/{equity_id}/price/import-historical", response_model=Dict[str, Any])
async def import_historical_prices(
        equity_id: int,
        historical_data: List[Tuple[datetime, Decimal]] = Body(..., description="Historical price data"),
        source: str = Body("historical_import", description="Data source"),
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme)
):
    """Import bulk historical price data for an equity."""
    return await controller.bulk_import_historical_prices(
        equity_id=equity_id,
        historical_data=historical_data,
        source=source,
        user_token=token
    )


@equity_router.delete("/{equity_id}/price/data", response_model=Dict[str, Any])
async def delete_price_data(
        equity_id: int,
        controller: EquityController = Depends(get_equity_controller),
        token: str = Depends(oauth2_scheme),
        start_date: Optional[datetime] = Query(None, description="Start date for deletion"),
        end_date: Optional[datetime] = Query(None, description="End date for deletion")
):
    """Delete price data for an equity within date range."""
    return await controller.delete_price_data(equity_id, start_date, end_date, token)


# === Health and Monitoring ===

@equity_router.get("/health", response_model=Dict[str, Any])
async def health_check(
        controller: EquityController = Depends(get_equity_controller)
):
    """Health check for the equity service."""
    return await controller.health_check()


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# The router is ready to be included in the main FastAPI application
# Example usage in main app:
#
# from fastapi import FastAPI
# from equity.src.api.equity_router import equity_router
#
# app = FastAPI()
# app.include_router(equity_router, prefix="/api/v1/equities", tags=["equities"])
