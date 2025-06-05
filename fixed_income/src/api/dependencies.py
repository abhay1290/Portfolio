import logging
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from fixed_income.src.config import settings
from fixed_income.src.database import get_db

logger = logging.getLogger(__name__)

# Security dependencies
security = HTTPBearer()

# Database dependency
db_dependency = Annotated[Session, Depends(get_db)]


# Authentication dependency
async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if settings.AUTH_DISABLED:
        return {"sub": "system@internal", "roles": ["admin"]}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/verify-token",
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error connecting to auth service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )


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
