from fastapi import FastAPI
from Portfolios import PortfolioAPIs

app = FastAPI()

# Include the portfolio router
app.include_router(PortfolioAPIs.router)
#app.include_router(EquityAPIs.router)

@app.get("/{name}")
def read_api(name: str):
    return {"Welcome": name}



