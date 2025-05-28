import logging

from fastapi import FastAPI

from Equities.api.equity_routers_setup import dividend_router, equity_router

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
logger.info("Logging is enabled!")

app = FastAPI()

# Include routers

# app.include_router(zero_bond_router)
# app.include_router(fixed_bond_router)
# app.include_router(callable_bond_router)
# app.include_router(putable_bond_router)
# app.include_router(floater_bond_router)
# app.include_router(sinking_bond_router)

app.include_router(equity_router)
app.include_router(dividend_router)

# Include router in app
# app.include_router(bond_router.router)
