import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers from a centralized module
from equity.src.api.routers.equity_routers_setup import (
    acquisition_router,
    bankruptcy_router,
    delisting_router,
    distribution_router,
    dividend_router,
    equity_router,
    exchange_offer_router,
    liquidation_router,
    merger_router,
    reorganization_router,
    return_of_capital_router,
    reverse_split_router,
    rights_issue_router,
    special_dividend_router,
    spin_off_router,
    stock_dividend_router,
    stock_split_router,
    subscription_router,
    tender_offer_router,
    warrant_exercise_router
)
from equity.src.config import SERVICE_NAME, VERSION

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("equity_service.log")
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Equity Service",
    version="1.0.0",
    description="Microservice for equity and corporate action management",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Organize routers by category
EQUITY_ROUTERS = [
    (equity_router, "/api/v1/equities", "equities")
]

DIVIDEND_ROUTERS = [
    (dividend_router, "dividends"),
    (special_dividend_router, "special-dividends"),
    (distribution_router, "distributions"),
    (return_of_capital_router, "return-of-capital")
]

REORGANIZATION_ROUTERS = [
    (stock_split_router, "stock-splits"),
    (stock_dividend_router, "stock-dividends"),
    (reverse_split_router, "reverse-splits"),
    (spin_off_router, "spin-offs")
]

CORPORATE_RESTRUCTURING_ROUTERS = [
    (merger_router, "mergers"),
    (acquisition_router, "acquisitions"),
    (tender_offer_router, "tender-offers"),
    (exchange_offer_router, "exchange-offers")
]

ISSUANCE_ROUTERS = [
    (rights_issue_router, "rights-issues"),
    (warrant_exercise_router, "warrant-exercises"),
    (subscription_router, "subscriptions")
]

TERMINATION_ROUTERS = [
    (delisting_router, "delisting"),
    (bankruptcy_router, "bankruptcies"),
    (liquidation_router, "liquidations"),
    (reorganization_router, "reorganizations")
]

# Register all routers
for router, tag in DIVIDEND_ROUTERS:
    app.include_router(
        router,
        prefix=f"/api/v1/corporate-actions",  # Base prefix
        tags=["Cash Distributions", tag]  # Group tag
    )

for router, tag in REORGANIZATION_ROUTERS:
    app.include_router(
        router,
        prefix=f"/api/v1/corporate-actions",
        tags=["Reorganization", tag]  # Group tag
    )

for router, tag in CORPORATE_RESTRUCTURING_ROUTERS:
    app.include_router(
        router,
        prefix=f"/api/v1/corporate-actions",  # Base prefix
        tags=["Corporate Reorganization", tag]  # Group tag
    )

for router, tag in ISSUANCE_ROUTERS:
    app.include_router(
        router,
        prefix=f"/api/v1/corporate-actions",
        tags=["Issuance", tag]  # Group tag
    )
for router, tag in TERMINATION_ROUTERS:
    app.include_router(
        router,
        prefix=f"/api/v1/corporate-actions",
        tags=["Termination", tag]  # Group tag
    )


@app.get("/health", tags=["monitoring"])
async def health_check():
    """Endpoint for service health monitoring"""
    return {
        "status": "healthy",
        "version": VERSION,
        "service": SERVICE_NAME,
        # Additional health indicators:
        "database_status": "connected",  # You would check DB connection
        "redis_status": "connected"  # And other dependencies
    }

# @app.on_event("startup")
# async def startup_event():
#     """Initialize service on startup"""
#     logger.info("Starting Equity Service")
#     # Add any initialization logic here
#
#
# @app.on_event("shutdown")
# async def shutdown_event():
#     """Cleanup on service shutdown"""
#     logger.info("Shutting down Equity Service")
#     # Add any cleanup logic here
