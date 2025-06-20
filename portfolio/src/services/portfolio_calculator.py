from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional

from portfolio.src.model import Constituent, Portfolio
from portfolio.src.model.enums import AssetClassEnum
from portfolio.src.services.portfolio_service_config import PortfolioServiceConfig


class PortfolioCalculator:
    """Handles all portfolio calculations"""

    def __init__(self, config: PortfolioServiceConfig):
        self.config = config

    def calculate_total_market_value(self, constituents: List[Constituent]) -> Decimal:
        """Calculate total market value with proper decimal handling"""
        total = Decimal('0')
        for constituent in constituents:
            if constituent.units and constituent.market_price:
                market_value = (Decimal(str(constituent.units)) *
                                Decimal(str(constituent.market_price)))
                constituent.market_value = market_value.quantize(
                    self.config.DECIMAL_PRECISION, rounding=ROUND_HALF_UP
                )
                total += constituent.market_value
        return total.quantize(self.config.DECIMAL_PRECISION, rounding=ROUND_HALF_UP)

    def calculate_nav_per_share(self, portfolio: Portfolio) -> Optional[Decimal]:
        """Calculate NAV per share"""
        if not portfolio.total_market_value or not portfolio.total_shares_outstanding:
            return None
        nav = (Decimal(str(portfolio.total_market_value)) /
               Decimal(str(portfolio.total_shares_outstanding)))
        return nav.quantize(self.config.DECIMAL_PRECISION, rounding=ROUND_HALF_UP)

    def calculate_asset_allocation(self, constituents: List[Constituent]) -> Dict[str, Decimal]:
        """Calculate asset allocation percentages"""
        allocation = {}
        total_value = sum(c.market_value or Decimal('0') for c in constituents)

        if total_value == 0:
            return allocation

        for asset_class in AssetClassEnum:
            class_value = sum(
                c.market_value or Decimal('0')
                for c in constituents
                if c.asset_class == asset_class
            )
            if class_value > 0:
                allocation[asset_class.name] = (class_value / total_value * 100).quantize(
                    self.config.PERCENT_PRECISION, rounding=ROUND_HALF_UP
                )
        return allocation

    def calculate_currency_exposure(self, constituents: List[Constituent]) -> Dict[str, Decimal]:
        """Calculate currency exposure percentages"""
        exposure = {}
        total_value = sum(c.market_value or Decimal('0') for c in constituents)

        if total_value == 0:
            return exposure

        currency_values = {}
        for constituent in constituents:
            currency = constituent.currency
            currency_values[currency] = currency_values.get(currency, Decimal('0')) + (
                    constituent.market_value or Decimal('0')
            )

        for currency, value in currency_values.items():
            exposure[currency] = (value / total_value * 100).quantize(
                self.config.PERCENT_PRECISION, rounding=ROUND_HALF_UP
            )
        return exposure
