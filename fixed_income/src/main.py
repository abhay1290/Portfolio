import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from fixed_income.src.api.routers.bond_routers_setup import callable_bond_router, fixed_bond_router, \
    floater_bond_router, putable_bond_router, sinking_bond_router, zero_bond_router
from fixed_income.src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fixed_income_service.log")
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Fixed Income Service",
    version="1.0.0",
    description="Microservice for bonds and fixed income products management",
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
app.include_router(zero_bond_router)
app.include_router(fixed_bond_router)
app.include_router(callable_bond_router)
app.include_router(putable_bond_router)
app.include_router(floater_bond_router)
app.include_router(sinking_bond_router)
