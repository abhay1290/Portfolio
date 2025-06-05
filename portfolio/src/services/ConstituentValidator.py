# Validation Service Layer
from typing import List

from portfolio.src.api.schemas.constituent_schema import PortfolioBondRequest, PortfolioEquityRequest
from portfolio.src.api.schemas.portfolio_schema import PortfolioRequest


class ConstituentValidator:
    def __init__(self, equity_service, bond_service):
        self.equity_service = equity_service
        self.bond_service = bond_service

    async def validate_and_fetch_constituents(self, request: PortfolioRequest):
        """
        Validates constituent IDs and fetches/create missing ones
        Returns validated constituents ready for portfolio creation
        """
        validated_data = {
            "equities": await self._process_equities(request.equity_ids),
            "bonds": await self._process_bonds(request.bond_ids)
        }
        return validated_data

    async def _process_equities(self, equity_requests: List[PortfolioEquityRequest]):
        results = []
        for req in equity_requests:
            equity = await self.equity_service.get_or_create(req.equity_id)
            if not equity:
                raise ValueError(f"Equity {req.equity_id} not found and could not be created")
            results.append({
                "equity_id": equity.id,
                **req.model_dump(exclude={"equity_id"})
            })
        return results

    async def _process_bonds(self, bond_requests: List[PortfolioBondRequest]):
        results = []
        for req in bond_requests:
            bond = await self.bond_service.get_or_create(req.bond_id)
            if not bond:
                raise ValueError(f"Bond {req.bond_id} not found and could not be created")
            results.append({
                "bond_id": bond.id,
                **req.model_dump(exclude={"bond_id"})
            })
        return results
