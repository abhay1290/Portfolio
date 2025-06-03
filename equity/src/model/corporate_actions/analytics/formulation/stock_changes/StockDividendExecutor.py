import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from equity.src.model.corporate_actions.analytics.formulation.CorporateActionExecutorBase import \
    CorporateActionExecutorBase
from equity.src.model.corporate_actions.model.stock_changes.StockDividend import StockDividend
from equity.src.utils.Decorators import performance_monitor
from equity.src.utils.Exceptions import StockDividendValidationError

logger = logging.getLogger(__name__)


class StockDividendExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize stock dividend-specific attributes"""
        if not isinstance(self.corporate_action, StockDividend):
            raise StockDividendValidationError("Must provide a StockDividend instance")

        self.stock_dividend = self.corporate_action

        # Initialize calculation results
        self.additional_shares = None
        self.new_shares_outstanding = None
        self.new_market_price = None
        self.total_fair_value = None

        # Validation and adjustment
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust stock dividend dates"""
        self.stock_dividend.declaration_date = self._adjust_date(
            datetime.combine(self.stock_dividend.declaration_date, datetime.min.time())
        )

        self.stock_dividend.distribution_date = self._adjust_date(
            datetime.combine(self.stock_dividend.distribution_date, datetime.min.time())
        )

        if self.stock_dividend.ex_dividend_date:
            self.stock_dividend.ex_dividend_date = self._adjust_date(
                datetime.combine(self.stock_dividend.ex_dividend_date, datetime.min.time())
            )

        if self.stock_dividend.declaration_date >= self.stock_dividend.distribution_date:
            self.validation_errors.append("Declaration date must be before distribution date")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for stock dividend execution"""
        errors = []

        # Validate dividend ratio
        if self.stock_dividend.dividend_shares_per_held <= 0:
            errors.append("Dividend shares per held must be positive")

        # Validate equity state
        if not self.equity.market_price or self.equity.market_price <= 0:
            errors.append("Equity market price must be positive")

        if not self.equity.shares_outstanding or self.equity.shares_outstanding <= 0:
            errors.append("Equity shares outstanding must be positive")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate stock dividend financial impacts"""
        # Calculate additional shares to be distributed
        self._calculate_additional_shares()

        # Calculate new shares outstanding
        self._calculate_new_shares_outstanding()

        # Calculate new market price (adjusted for dilution)
        self._calculate_new_market_price()

        # Calculate total fair value of stock dividend
        self._calculate_total_fair_value()

        impact_data = {
            'old_shares_outstanding': float(self.equity.shares_outstanding),
            'additional_shares': float(self.additional_shares),
            'new_shares_outstanding': float(self.new_shares_outstanding),
            'old_market_price': float(self.equity.market_price),
            'new_market_price': float(self.new_market_price),
            'dividend_shares_per_held': float(self.stock_dividend.dividend_shares_per_held),
            'total_fair_value': float(self.total_fair_value) if self.total_fair_value else 0.0,
            'dividend_percentage': self.stock_dividend.dividend_percentage or 0.0
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute stock dividend and adjust equity values"""
        original_state = {
            'market_price': float(self.equity.market_price),
            'shares_outstanding': float(self.equity.shares_outstanding),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None
        }

        # Apply stock dividend adjustments
        self._apply_stock_dividend_adjustments()

        # Update stock dividend model with calculated values
        self.stock_dividend.fair_market_value = self.total_fair_value

        new_state = {
            'market_price': float(self.equity.market_price),
            'shares_outstanding': float(self.equity.shares_outstanding),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None
        }

        return {
            'original_state': original_state,
            'new_state': new_state,
            'adjustments_applied': {
                'shares_increase': float(self.additional_shares),
                'price_adjustment': float(original_state['market_price'] - new_state['market_price']),
                'total_dividend_value': float(self.total_fair_value) if self.total_fair_value else 0.0
            }
        }

    def post_execution_validation(self) -> bool:
        """Validate execution results"""
        errors = []

        # Validate shares increase
        if self.equity.shares_outstanding <= float(self.equity.shares_outstanding) + float(self.additional_shares):
            errors.append("Shares outstanding should increase after stock dividend")

        # Validate market cap (should remain approximately the same)
        calculated_market_cap = self.equity.market_price * self.equity.shares_outstanding
        if self.equity.market_cap and abs(float(calculated_market_cap) - float(self.equity.market_cap)) > 0.01:
            errors.append("Market cap consistency validation failed")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _calculate_additional_shares(self):
        """Calculate additional shares to be distributed"""
        self.additional_shares = Decimal(str(self.equity.shares_outstanding)) * Decimal(
            str(self.stock_dividend.dividend_shares_per_held))

    def _calculate_new_shares_outstanding(self):
        """Calculate new total shares outstanding"""
        self.new_shares_outstanding = Decimal(str(self.equity.shares_outstanding)) + self.additional_shares

    def _calculate_new_market_price(self):
        """Calculate new market price after dilution"""
        dilution_factor = self.new_shares_outstanding / Decimal(str(self.equity.shares_outstanding))
        self.new_market_price = Decimal(str(self.equity.market_price)) / dilution_factor

    def _calculate_total_fair_value(self):
        """Calculate total fair value of stock dividend"""
        if self.stock_dividend.fair_market_value:
            self.total_fair_value = Decimal(str(self.stock_dividend.fair_market_value)) * self.additional_shares
        else:
            # Use current market price as fair value
            self.total_fair_value = Decimal(str(self.equity.market_price)) * self.additional_shares

    def _apply_stock_dividend_adjustments(self):
        """Apply stock dividend adjustments to equity"""
        # Update shares outstanding
        self.equity.shares_outstanding = self.new_shares_outstanding

        # Update market price (adjusted for dilution)
        self.equity.market_price = self.new_market_price

        # Market cap should remain approximately the same
        self.equity.market_cap = self.equity.market_price * self.equity.shares_outstanding
