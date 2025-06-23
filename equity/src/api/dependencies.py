import logging
from typing import Annotated, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from equity.src.config import settings
from equity.src.database.session import get_db

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


# Enhanced authentication dependency
async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Enhanced authentication with better error handling and user context"""
    if settings.AUTH_DISABLED:
        return {
            "sub": "system@internal",
            "roles": ["admin"],
            "access_token": "system_token",
            "permissions": ["read", "write", "admin"]
        }

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

        user_data = response.json()
        # Add access token for downstream service calls
        user_data["access_token"] = credentials.credentials
        return user_data

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


# Base service client with enhanced functionality
class BaseServiceClient:
    """Base class for all external service clients"""

    def __init__(self, base_url: str, service_name: str):
        self.base_url = base_url.rstrip('/')
        self.service_name = service_name
        self.timeout = settings.EXTERNAL_SERVICE_TIMEOUT

    async def _make_request(
            self,
            method: str,
            endpoint: str,
            token: str,
            timeout: Optional[int] = None,
            **kwargs
    ) -> dict:
        """Make HTTP request with comprehensive error handling"""
        try:
            client = await http_manager.get_client()

            # Use custom timeout or default
            request_timeout = timeout or self.timeout

            response = await client.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "X-Service-Name": "equity-service",
                    "X-Request-ID": self._generate_request_id()
                },
                timeout=request_timeout,
                **kwargs
            )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"{self.service_name} HTTP error {e.response.status_code}: {e.response.text}")

            # Map common HTTP errors
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resource not found in {self.service_name}"
                )
            elif e.response.status_code == 403:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to {self.service_name}"
                )
            else:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"{self.service_name} error: {e.response.text[:100]}"
                )

        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to {self.service_name}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{self.service_name} timeout"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error to {self.service_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{self.service_name} unavailable"
            )

    def _generate_request_id(self) -> str:
        """Generate unique request ID for tracing"""
        import uuid
        return str(uuid.uuid4())


# Portfolio service client
class PortfolioServiceClient:
    def __init__(self):
        self.base_url = settings.PORTFOLIO_SERVICE_URL
        self.timeout = settings.EXTERNAL_SERVICE_TIMEOUT

    async def get_portfolio(self, portfolio_id: str, token: str):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/portfolios/{portfolio_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Portfolio service error: {str(e)}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Error fetching portfolio from portfolio service"
            )
        except httpx.RequestError as e:
            logger.error(f"Error connecting to portfolio service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Portfolio service unavailable"
            )


def get_portfolio_service():
    return PortfolioServiceClient()


portfolio_service_dependency = Annotated[PortfolioServiceClient, Depends(get_portfolio_service)]
