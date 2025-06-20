import asyncio
import logging
from decimal import Decimal
from typing import List

from portfolio.src.api.dependencies import EquityServiceClient, FixedIncomeServiceClient
from portfolio.src.model import Constituent
from portfolio.src.model.enums import AssetClassEnum
from portfolio.src.services.portfolio_service_config import PortfolioServiceConfig

logger = logging.getLogger(__name__)


class PriceService:
    """Handles market price updates"""

    def __init__(self,
                 equity_client: EquityServiceClient,
                 fixed_income_client: FixedIncomeServiceClient,
                 config: PortfolioServiceConfig):
        self.equity_client = equity_client
        self.fixed_income_client = fixed_income_client
        self.config = config

    async def update_market_prices(self, constituents: List[Constituent], user_token: str) -> None:
        """Update market prices in batches"""
        equity_ids = [
            c.asset_id for c in constituents
            if c.asset_class == AssetClassEnum.EQUITY
        ]
        bond_ids = [
            c.asset_id for c in constituents
            if c.asset_class == AssetClassEnum.FIXED_INCOME
        ]

        # Process in batches
        tasks = []
        for i in range(0, len(equity_ids), self.config.BATCH_SIZE):
            batch = equity_ids[i:i + self.config.BATCH_SIZE]
            tasks.append(self._update_equity_prices(batch, constituents, user_token))

        for i in range(0, len(bond_ids), self.config.BATCH_SIZE):
            batch = bond_ids[i:i + self.config.BATCH_SIZE]
            tasks.append(self._update_bond_prices(batch, constituents, user_token))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _update_equity_prices(self, equity_ids: List[str], constituents: List[Constituent],
                                    user_token: str) -> None:
        """Update equity prices"""
        try:
            equity_prices = await self.equity_client.get_equity_prices(equity_ids, user_token)
            for constituent in constituents:
                if (constituent.asset_class == AssetClassEnum.EQUITY and
                        str(constituent.asset_id) in equity_prices.get('prices', {})):
                    constituent.market_price = Decimal(
                        str(equity_prices['prices'][str(constituent.asset_id)]))
        except Exception as e:
            logger.warning(f"Failed to update equity prices: {str(e)}")

    async def _update_bond_prices(self, bond_ids: List[str], constituents: List[Constituent], user_token: str) -> None:
        """Update bond prices"""
        try:
            bond_prices = await self.fixed_income_client.get_bond_prices(bond_ids, user_token)
            for constituent in constituents:
                if (constituent.asset_class == AssetClassEnum.FIXED_INCOME and
                        str(constituent.asset_id) in bond_prices.get('prices', {})):
                    constituent.market_price = Decimal(
                        str(bond_prices['prices'][str(constituent.asset_id)]))
        except Exception as e:
            logger.warning(f"Failed to update bond prices: {str(e)}")
