import logging

from fastapi import Depends, FastAPI

from portfolio.src.api.routers.router_setup import portfolio_router
from portfolio.src.api.schemas.portfolio_schema import PortfolioRequest, PortfolioResponse
from portfolio.src.config import settings
from portfolio.src.services import portfolio_service
from portfolio.src.services.ConstituentValidator import ConstituentValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("portfolio_service.log")
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Portfolio Service",
    version="1.0.0",
    description="Microservice for Portfolio management",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)


@app.get("/health", tags=["monitoring"])
async def health_check():
    """Endpoint for service health monitoring"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "service": settings.SERVICE_NAME,
        # Additional health indicators:
        "database_status": "connected",  # You would check DB connection
        "redis_status": "connected"  # And other dependencies
    }


# Include routers
app.include_router(portfolio_router)


# In your FastAPI endpoint
@app.post("/portfolios", response_model=PortfolioResponse)
async def create_portfolio(
        request: PortfolioRequest,
        validator: ConstituentValidator = Depends()
):
    validated = await validator.validate_and_fetch_constituents(request)

    # Create portfolio with validated constituents
    portfolio = await portfolio_service.create_with_constituents(
        portfolio_data=request,
        equities=validated["equities"],
        bonds=validated["bonds"]
    )

    return portfolio
