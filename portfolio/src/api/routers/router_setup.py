from portfolio.src.api.routers.crud_router import PortfolioGenericRouter
from portfolio.src.api.schemas.portfolio_schema import PortfolioRequest, PortfolioResponse
from portfolio.src.model.Portfolio import Portfolio

portfolio_router = PortfolioGenericRouter(
    model=Portfolio,
    create_schema=PortfolioRequest,
    response_schema=PortfolioResponse,
    base_path=Portfolio.API_Path,

).router
