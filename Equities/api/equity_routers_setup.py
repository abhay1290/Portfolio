from Equities.api.corporate_action_crud_router import CorporateActionGenericRouter
from Equities.api.corporate_action_schema.cash_distribution.dividend_schema import DividendRequest, DividendResponse
from Equities.api.equity_crud_router import EquityGenericRouter
from Equities.api.equity_schema.Equity_Schema import EquityRequest, EquityResponse
from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase
from Equities.corporate_actions.model.cash_distribution.Dividend import Dividend
from Equities.model.Equity import Equity

equity_router = EquityGenericRouter(
    model=Equity,
    create_schema=EquityRequest,
    response_schema=EquityResponse,
    base_path=Equity.API_Path,
    tags=["Equity"]
).router

dividend_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Dividend,
    create_schema=DividendRequest,
    response_schema=DividendResponse,
    base_path=Dividend.API_Path,
    tags=["Dividend"]
).router
