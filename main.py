import logging

from fastapi import FastAPI

from Equities.api.equity_routers_setup import acquisition_router, bankruptcy_router, delisting_router, \
    distribution_router, \
    dividend_router, equity_router, \
    exchange_offer_router, liquidation_router, merger_router, reorganization_router, return_of_capital_router, \
    reverse_split_router, \
    rights_issue_router, \
    special_dividend_router, spin_off_router, stock_dividend_router, \
    stock_split_router, subscription_router, tender_offer_router, warrant_exercise_router

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
app.include_router(special_dividend_router)
app.include_router(distribution_router)
app.include_router(return_of_capital_router)

app.include_router(stock_split_router)
app.include_router(stock_dividend_router)
app.include_router(reverse_split_router)
app.include_router(spin_off_router)

app.include_router(merger_router)
app.include_router(acquisition_router)
app.include_router(tender_offer_router)
app.include_router(exchange_offer_router)

app.include_router(rights_issue_router)
app.include_router(warrant_exercise_router)
app.include_router(subscription_router)

app.include_router(delisting_router)
app.include_router(bankruptcy_router)
app.include_router(liquidation_router)
app.include_router(reorganization_router)

# Include router in app
# app.include_router(bond_router.router)
