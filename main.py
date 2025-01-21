from fastapi import FastAPI

from CorporateActions import CorporateActionAPIs
from Equities import EquityAPIs
from Portfolios import PortfolioAPIs

app = FastAPI()

# Include routers
app.include_router(PortfolioAPIs.portfolio_router)
app.include_router(EquityAPIs.equity_router)
app.include_router(CorporateActionAPIs.ca_router)

@app.get("/{name}")
def read_api(name: str):
    return {"Welcome": name}


