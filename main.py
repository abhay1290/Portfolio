import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from CorporateActions.CorporateAction import CorporateAction
from CorporateActions.corporate_action_schema import CorporateActionCreate, CorporateActionResponse
from Equities.Equity import Equity
from Equities.equity_schema import EquityCreate, EquityResponse
from FixedIncome.Bond import Bond
from FixedIncome.api.bond_schema import BondCreate, BondResponse
from Portfolios.Portfolio import Portfolio
from Portfolios.portfolio_schema import PortfolioCreate, PortfolioResponse
from crud_router import GenericRouter

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
logger.info("Logging is enabled!")

app = FastAPI()

portfolio_router = GenericRouter(
    model=Portfolio,
    create_schema=PortfolioCreate,
    response_schema=PortfolioResponse,
    base_path=Portfolio.API_Path,
    tags=["Portfolio"]
).router

equity_router = GenericRouter(
    model=Equity,
    create_schema=EquityCreate,
    response_schema=EquityResponse,
    base_path=Equity.API_Path,
    tags=["Equity"]
).router

bond_router = GenericRouter(
    model=Bond,
    create_schema=BondCreate,
    response_schema=BondResponse,
    base_path=Bond.API_Path,
    tags=["Fixed Income"]
).router

corporate_action_router = GenericRouter(
    model=CorporateAction,
    create_schema=CorporateActionCreate,
    response_schema=CorporateActionResponse,
    base_path=CorporateAction.API_Path,
    tags=["Corporate Action"]
).router

# Include routers
app.include_router(portfolio_router)
app.include_router(equity_router)
app.include_router(bond_router)
app.include_router(corporate_action_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.get("/{name}")
def read_api(name: str):
    return {"Welcome": name}
