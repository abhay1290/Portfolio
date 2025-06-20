import logging
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from portfolio.src.config import settings
from portfolio.src.database.session import get_db

logger = logging.getLogger(__name__)

# Security dependencies
security = HTTPBearer()

# Database dependency
db_dependency = Annotated[Session, Depends(get_db)]


# HTTP Client pool for better performance
class HTTPClientManager:
    def __init__(self):
        self.client = None

    async def get_client(self) -> httpx.AsyncClient:
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.EXTERNAL_SERVICE_TIMEOUT),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
            )
        return self.client

    async def close(self):
        if self.client:
            await self.client.aclose()


http_manager = HTTPClientManager()


# Authentication dependency with improved error handling
async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    if settings.AUTH_DISABLED:
        return {"sub": "system@internal", "roles": ["admin"]}

    try:
        client = await http_manager.get_client()
        response = await client.get(
            f"{settings.AUTH_SERVICE_URL}/verify-token",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )

        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif response.status_code != 200:
            logger.warning(f"Auth service returned {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
            )

        return response.json()

    except httpx.TimeoutException:
        logger.error("Timeout connecting to auth service")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service timeout",
        )
    except httpx.RequestError as e:
        logger.error(f"Error connecting to auth service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )


# Base service client with common functionality
class BaseServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.timeout = settings.EXTERNAL_SERVICE_TIMEOUT

    async def _make_request(self, method: str, endpoint: str, token: str, **kwargs) -> dict:
        """Make HTTP request with proper error handling"""
        try:
            client = await http_manager.get_client()
            response = await client.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                headers={"Authorization": f"Bearer {token}"},
                **kwargs
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Service error: {e.response.text[:100]}"
            )
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to {self.base_url}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service timeout"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error to {self.base_url}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unavailable"
            )


# Equity service client with improved error handling
class EquityServiceClient(BaseServiceClient):
    def __init__(self):
        super().__init__(settings.EQUITY_SERVICE_URL)

    async def get_equity_instrument(self, equity_id: int, token: str) -> dict:
        """Get equity instrument by ID"""
        return await self._make_request(
            "GET",
            f"/api/v1/equities/{equity_id}",
            token
        )

    async def get_equity_instruments_by_portfolio(self, portfolio_id: int, token: str) -> dict:
        """Get equity instruments by portfolio ID"""
        return await self._make_request(
            "GET",
            f"/api/v1/equities/by-portfolio/{portfolio_id}",
            token
        )

    async def get_equity_prices(self, equity_ids: list[int], token: str) -> dict:
        """Batch get equity prices"""
        return await self._make_request(
            "POST",
            "/api/v1/equities/prices",
            token,
            json={"equity_ids": equity_ids}
        )


# Fixed Income service client with improved error handling
class FixedIncomeServiceClient(BaseServiceClient):
    def __init__(self):
        super().__init__(settings.FIXED_INCOME_SERVICE_URL)

    async def get_fixed_income_instrument(self, fixed_income_id: int, token: str) -> dict:
        """Get fixed income instrument by ID"""
        return await self._make_request(
            "GET",
            f"/api/v1/fixed_income/{fixed_income_id}",
            token
        )

    async def get_fixed_income_instruments_by_portfolio(self, portfolio_id: int, token: str) -> dict:
        """Get fixed income instruments by portfolio ID"""
        return await self._make_request(
            "GET",
            f"/api/v1/fixed_income/by-portfolio/{portfolio_id}",
            token
        )

    async def get_bond_prices(self, bond_ids: list[int], token: str) -> dict:
        """Batch get bond prices"""
        return await self._make_request(
            "POST",
            "/api/v1/fixed_income/prices",
            token,
            json={"bond_ids": bond_ids}
        )


# Dependency providers
def get_equity_service() -> EquityServiceClient:
    return EquityServiceClient()


def get_fixed_income_service() -> FixedIncomeServiceClient:
    return FixedIncomeServiceClient()


# Typed dependencies
equity_service_dependency = Annotated[EquityServiceClient, Depends(get_equity_service)]
fixed_income_service_dependency = Annotated[FixedIncomeServiceClient, Depends(get_fixed_income_service)]
auth_dependency = Annotated[dict, Depends(get_current_user)]


# Cleanup function for graceful shutdown
async def cleanup_http_clients():
    await http_manager.close()


# Additional helper functions for better error handling
class ServiceError(Exception):
    """Custom exception for service errors"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def handle_service_error(func):
    """Decorator for handling service errors"""

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ServiceError as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    return wrapper
