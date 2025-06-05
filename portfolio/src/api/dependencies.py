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


# Equity service client
class EquityServiceClient:
    def __init__(self):
        self.base_url = settings.EQUITY_SERVICE_URL
        self.timeout = settings.EXTERNAL_SERVICE_TIMEOUT

    async def get_equity_instrument(self, equity_id: str, token: str):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/equities/{equity_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"equity_service error: {str(e)}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Error fetching equity instrument from equity_service"
            )
        except httpx.RequestError as e:
            logger.error(f"Error connecting to equity_service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="equity_service unavailable"
            )

    async def get_equity_instruments_by_portfolio(self, portfolio_id: str, token: str):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/equities/by-portfolio/{portfolio_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"equity_service error: {str(e)}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Error fetching equities from equity_service"
            )
        except httpx.RequestError as e:
            logger.error(f"Error connecting to equity_service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="equity_service unavailable"
            )


def get_equity_service():
    return EquityServiceClient()


equity_service_dependency = Annotated[EquityServiceClient, Depends(get_equity_service)]


# Fixed Income service client
class FixedIncomeServiceClient:
    def __init__(self):
        self.base_url = settings.FIXED_INCOME_SERVICE_URL
        self.timeout = settings.EXTERNAL_SERVICE_TIMEOUT

    async def get_fixed_income_instrument(self, fixed_income_id: str, token: str):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/fixed_income/{fixed_income_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"fixed_income_service error: {str(e)}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Error fetching fixed income instrument from fixed_income_service"
            )
        except httpx.RequestError as e:
            logger.error(f"Error connecting to fixed_income_service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="fixed_income_service unavailable"
            )

    async def get_fixed_income_instruments_by_portfolio(self, portfolio_id: str, token: str):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/fixed_income/by-portfolio/{portfolio_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"fixed_income_service error: {str(e)}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Error fetching fixed income instruments from fixed_income_service"
            )
        except httpx.RequestError as e:
            logger.error(f"Error connecting to fixed_income_service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="fixed_income_service unavailable"
            )


def get_fixed_income_service():
    return FixedIncomeServiceClient()


fixed_income_service_dependency = Annotated[FixedIncomeServiceClient, Depends(get_fixed_income_service)]
