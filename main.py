from fastapi import FastAPI
from CorporateActions.CorporateAction import CorporateAction
from CorporateActions.corporate_action_schema import CorporateActionCreate, CorporateActionResponse
from Equities.Equity import Equity
from Equities.equity_schema import EquityCreate, EquityResponse
from Portfolios.Portfolio import Portfolio
from Portfolios.portfolio_schema import PortfolioCreate, PortfolioResponse

from crud_router import GenericRouter

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
app.include_router(corporate_action_router)


@app.get("/{name}")
def read_api(name: str):
    return {"Welcome": name}


