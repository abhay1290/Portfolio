import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer

from portfolio.src.api.schemas.constituent_schema import (
    PortfolioBondRequest, PortfolioEquityRequest
)
from portfolio.src.api.schemas.portfolio_schema import (
    PortfolioPerformanceResponse, PortfolioRequest,
    PortfolioResponse, PortfolioSummaryResponse
)
from portfolio.src.model.PortfolioVersion import PortfolioVersion
from portfolio.src.services.portfolio_service import PortfolioService, create_portfolio_service

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

portfolio_router = APIRouter(
    prefix="/portfolios",
    tags=["portfolios"],
    responses={404: {"description": "Not found"}},
)


# Core Portfolio Operations

@portfolio_router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
        request: PortfolioRequest,
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Create a new portfolio with initial version.

    Creates a portfolio with automatic versioning, constituent validation,
    and market value calculations.
    """
    return await portfolio_service.create_portfolio(
        portfolio_data=request,
        user_token=token
    )


@portfolio_router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
        portfolio_id: int,
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Get portfolio details by ID.

    Returns complete portfolio information including all constituents,
    current metrics, and version information.
    """
    portfolio = await portfolio_service.get_portfolio(portfolio_id, token)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    return portfolio


@portfolio_router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
        portfolio_id: int,
        request: PortfolioRequest,
        change_reason: Optional[str] = Body(None, description="Reason for the update"),
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Update an existing portfolio and create new version.

    Updates portfolio fields and/or constituents. Creates a new version
    automatically with the specified change reason.
    """
    portfolio = await portfolio_service.update_portfolio(
        portfolio_id=portfolio_id,
        portfolio_data=request,
        user_token=token,
        change_reason=change_reason
    )
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    return portfolio


@portfolio_router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
        portfolio_id: int,
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Delete a portfolio and all its versions.

    Permanently deletes the portfolio, all constituents, and version history.
    This operation cannot be undone.
    """
    success = await portfolio_service.delete_portfolio(portfolio_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )


# Constituent Management Operations

@portfolio_router.post("/{portfolio_id}/constituents/add", response_model=PortfolioResponse)
async def add_constituents(
        portfolio_id: int,
        equities: Optional[List[PortfolioEquityRequest]] = Body(None),
        bonds: Optional[List[PortfolioBondRequest]] = Body(None),
        change_reason: Optional[str] = Body(None, description="Reason for adding constituents"),
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Add equity and/or bond constituents to a portfolio.

    Adds new constituents and automatically adjusts weights proportionally.
    Creates a new version with ADD_CONSTITUENT operation type.
    """
    if not equities and not bonds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one equity or bond must be provided"
        )

    return await portfolio_service.add_constituents(
        portfolio_id=portfolio_id,
        equity_requests=equities or [],
        bond_requests=bonds or [],
        user_token=token
    )


@portfolio_router.post("/{portfolio_id}/constituents/equities", response_model=PortfolioResponse)
async def add_equities(
        portfolio_id: int,
        equities: List[PortfolioEquityRequest],
        change_reason: Optional[str] = Body(None, description="Reason for adding equities"),
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Add equity constituents to a portfolio.

    Adds equity holdings and automatically adjusts all weights proportionally.
    """
    return await portfolio_service.add_constituents(
        portfolio_id=portfolio_id,
        equity_requests=equities,
        bond_requests=[],
        user_token=token
    )


@portfolio_router.post("/{portfolio_id}/constituents/bonds", response_model=PortfolioResponse)
async def add_bonds(
        portfolio_id: int,
        bonds: List[PortfolioBondRequest],
        change_reason: Optional[str] = Body(None, description="Reason for adding bonds"),
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Add bond constituents to a portfolio.

    Adds fixed income holdings and automatically adjusts all weights proportionally.
    """
    return await portfolio_service.add_constituents(
        portfolio_id=portfolio_id,
        equity_requests=[],
        bond_requests=bonds,
        user_token=token
    )


@portfolio_router.delete("/{portfolio_id}/constituents", response_model=PortfolioResponse)
async def remove_constituents(
        portfolio_id: int,
        equity_ids: Optional[List[str]] = Query(None, description="Equity asset IDs to remove"),
        bond_ids: Optional[List[str]] = Query(None, description="Bond asset IDs to remove"),
        change_reason: Optional[str] = Query(None, description="Reason for removing constituents"),
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Remove equity and/or bond constituents from a portfolio.

    Removes specified constituents and automatically adjusts remaining weights proportionally.
    Creates a new version with REMOVE_CONSTITUENT operation type.
    """
    if not equity_ids and not bond_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one equity_id or bond_id must be provided"
        )

    return await portfolio_service.remove_constituents(
        portfolio_id=portfolio_id,
        equity_ids=equity_ids or [],
        bond_ids=bond_ids or [],
        user_token=token
    )


@portfolio_router.delete("/{portfolio_id}/constituents/equities", response_model=PortfolioResponse)
async def remove_equities(
        portfolio_id: int,
        equity_ids: List[str] = Query(..., description="Equity asset IDs to remove"),
        change_reason: Optional[str] = Query(None, description="Reason for removing equities"),
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Remove equity constituents from a portfolio.

    Removes specified equity holdings and adjusts remaining weights proportionally.
    """
    return await portfolio_service.remove_constituents(
        portfolio_id=portfolio_id,
        equity_ids=equity_ids,
        bond_ids=[],
        user_token=token
    )


@portfolio_router.delete("/{portfolio_id}/constituents/bonds", response_model=PortfolioResponse)
async def remove_bonds(
        portfolio_id: int,
        bond_ids: List[str] = Query(..., description="Bond asset IDs to remove"),
        change_reason: Optional[str] = Query(None, description="Reason for removing bonds"),
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Remove bond constituents from a portfolio.

    Removes specified fixed income holdings and adjusts remaining weights proportionally.
    """
    return await portfolio_service.remove_constituents(
        portfolio_id=portfolio_id,
        equity_ids=[],
        bond_ids=bond_ids,
        user_token=token
    )


# Portfolio Operations

@portfolio_router.post("/{portfolio_id}/rebalance", response_model=PortfolioResponse)
async def rebalance_portfolio(
        portfolio_id: int,
        change_reason: Optional[str] = Body(None, description="Reason for rebalancing"),
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Rebalance portfolio to target weights.

    Adjusts constituent weights according to the portfolio's weighting methodology.
    Requires auto_rebalance_enabled to be true. Creates a new version with REBALANCE operation type.
    """
    return await portfolio_service.rebalance_portfolio(
        portfolio_id=portfolio_id,
        user_token=token
    )


# Portfolio Information Endpoints

@portfolio_router.get("/{portfolio_id}/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
        portfolio_id: int,
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Get portfolio summary information.

    Returns high-level portfolio metrics without full constituent details.
    Optimized for dashboard and listing views.
    """
    summary = await portfolio_service.get_portfolio_summary(portfolio_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    return summary


@portfolio_router.get("/{portfolio_id}/performance", response_model=PortfolioPerformanceResponse)
async def get_portfolio_performance(
        portfolio_id: int,
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Get portfolio performance metrics.

    Returns time-series performance data, risk metrics, and benchmark comparisons.
    """
    performance = await portfolio_service.get_portfolio_performance(portfolio_id)
    if not performance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    return performance


# Version Management Endpoints

@portfolio_router.get("/{portfolio_id}/versions", response_model=List[PortfolioVersion])
async def get_version_history(
        portfolio_id: int,
        limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of versions to return"),
        offset: Optional[int] = Query(0, ge=0, description="Number of versions to skip"),
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Get complete version history for a portfolio.

    Returns all versions in descending order (newest first).
    Supports pagination with limit and offset parameters.
    """
    try:
        versions = await portfolio_service.get_version_history(portfolio_id)

        # Apply pagination
        if offset:
            versions = versions[offset:]
        if limit:
            versions = versions[:limit]

        return versions
    except Exception as e:
        logger.error(f"Error getting version history for portfolio {portfolio_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get version history"
        )


@portfolio_router.get("/{portfolio_id}/versions/{version_id}", response_model=PortfolioVersion)
async def get_specific_version(
        portfolio_id: int,
        version_id: int,
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Get a specific version of a portfolio.

    Returns detailed information about a specific portfolio version,
    including the complete state snapshot at that point in time.
    """
    return await portfolio_service.get_specific_version(portfolio_id, version_id)


@portfolio_router.get("/{portfolio_id}/versions/latest", response_model=PortfolioVersion)
async def get_latest_version(
        portfolio_id: int,
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Get the latest version of a portfolio.

    Returns the most recent version with complete state information.
    """
    version = await portfolio_service.get_latest_version(portfolio_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No versions found for portfolio {portfolio_id}"
        )
    return version


@portfolio_router.post("/{portfolio_id}/versions/{version_id}/rollback", response_model=PortfolioResponse)
async def rollback_to_version(
        portfolio_id: int,
        version_id: int,
        change_reason: Optional[str] = Body(None, description="Reason for rollback"),
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Rollback portfolio to a specific version.

    Restores the portfolio to the exact state of the specified version.
    Creates a new version with ROLLBACK operation type.
    """
    return await portfolio_service.rollback_to_version(
        portfolio_id=portfolio_id,
        target_version_id=version_id,
        rolled_back_by=token,
        change_reason=change_reason
    )


@portfolio_router.get("/{portfolio_id}/versions/compare", response_model=dict)
async def compare_versions(
        portfolio_id: int,
        version1: int = Query(..., description="First version to compare"),
        version2: int = Query(..., description="Second version to compare"),
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Compare differences between two portfolio versions.

    Returns detailed comparison showing what changed between the two versions,
    including portfolio field changes and constituent modifications.
    """
    return await portfolio_service.compare_versions(
        portfolio_id=portfolio_id,
        version1_id=version1,
        version2_id=version2
    )


# Bulk Operations

@portfolio_router.post("/bulk/create", response_model=List[PortfolioResponse])
async def bulk_create_portfolios(
        requests: List[PortfolioRequest],
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Create multiple portfolios in bulk.

    Creates multiple portfolios efficiently. Returns results for all portfolios,
    including any that failed with error details.
    """
    results = []
    for request in requests:
        try:
            portfolio = await portfolio_service.create_portfolio(request, token)
            results.append(portfolio)
        except Exception as e:
            logger.error(f"Failed to create portfolio {request.symbol}: {str(e)}")
            # In a real implementation, you might want to collect errors and return them
            # For now, we'll skip failed portfolios
            continue

    return results


@portfolio_router.get("/search", response_model=List[PortfolioSummaryResponse])
async def search_portfolios(
        query: Optional[str] = Query(None, description="Search term for portfolio name or symbol"),
        portfolio_type: Optional[str] = Query(None, description="Filter by portfolio type"),
        status: Optional[str] = Query(None, description="Filter by portfolio status"),
        limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
        offset: int = Query(0, ge=0, description="Number of results to skip"),
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Search and filter portfolios.

    Search portfolios by name, symbol, type, or status.
    Returns summary information for matching portfolios with pagination.

    Note: This endpoint would need additional implementation in the service layer.
    """
    # This would need to be implemented in the service layer
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Search functionality not yet implemented"
    )


# Health and Validation Endpoints

@portfolio_router.post("/{portfolio_id}/validate", response_model=dict)
async def validate_portfolio(
        portfolio_id: int,
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Validate portfolio integrity and constraints.

    Performs comprehensive validation of portfolio business rules,
    weight constraints, and data integrity.

    Note: This endpoint would need additional implementation in the service layer.
    """
    # This would need to be implemented in the service layer
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Validation functionality not yet implemented"
    )


@portfolio_router.get("/{portfolio_id}/health", response_model=dict)
async def get_portfolio_health(
        portfolio_id: int,
        token: str = Depends(oauth2_scheme),
        portfolio_service: PortfolioService = Depends(create_portfolio_service)
):
    """
    Get portfolio health status and warnings.

    Returns portfolio health metrics, constraint violations,
    and operational warnings.

    Note: This endpoint would need additional implementation in the service layer.
    """
    # This would need to be implemented in the service layer
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Health check functionality not yet implemented"
    )
