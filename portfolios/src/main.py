import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from portfolios.src.config import settings

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
