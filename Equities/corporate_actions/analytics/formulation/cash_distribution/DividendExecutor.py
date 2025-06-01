import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.cash_distribution.Dividend import Dividend
from Equities.utils.Decorators import performance_monitor
from Equities.utils.Exceptions import DividendValidationError

logger = logging.getLogger(__name__)


class DividendExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize dividend-specific attributes"""
        if not isinstance(self.corporate_action, Dividend):
            raise DividendValidationError("Must provide a Dividend instance")

        self.dividend = self.corporate_action

        # Initialize calculation results
        self.net_dividend_amount = None
        self.eligible_outstanding_shares = None
        self.total_dividend_marketcap_in_dividend_currency = None
        self.dividend_impact_in_equity_currency = None
        self.price_adjustment = None

        # Validation and adjustment
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust dividend dates"""
        # Adjust dates according to calendar
        if self.dividend.ex_dividend_date:
            self.dividend.ex_dividend_date = self._adjust_date(
                datetime.combine(self.dividend.ex_dividend_date, datetime.min.time())
            )

        self.dividend.record_date = self._adjust_date(
            datetime.combine(self.dividend.record_date, datetime.min.time())
        )

        self.dividend.payment_date = self._adjust_date(
            datetime.combine(self.dividend.payment_date, datetime.min.time())
        )

        # Validate date sequence
        if self.dividend.ex_dividend_date and self.dividend.record_date:
            if self.dividend.ex_dividend_date >= self.dividend.record_date:
                self.validation_errors.append("Ex-dividend date must be before record date")

        if self.dividend.payment_date < self.dividend.record_date:
            self.validation_errors.append("Payment date cannot be before record date")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for dividend execution"""
        errors = []

        # Validate dividend amount
        if self.dividend.dividend_amount <= 0:
            errors.append("Dividend amount must be positive")

        # Validate shares
        if self.dividend.eligible_outstanding_shares <= 0:
            errors.append("Eligible outstanding shares must be positive")

        # Validate equity state
        if not self.equity.market_price or self.equity.market_price <= 0:
            errors.append("Equity market price must be positive")

        if not self.equity.shares_outstanding or self.equity.shares_outstanding <= 0:
            errors.append("Equity shares outstanding must be positive")

        # Validate currency consistency
        if self.dividend.currency != self.equity.currency:
            errors.append("Dividend currency must match equity currency")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate dividend financial impacts"""
        # Calculate net dividend amount after tax
        self._calculate_net_dividend_amount()

        # Calculate total dividend payout
        self._calculate_total_dividend_marketcap_in_dividend_currency()

        # Calculate market cap impact
        self._calculate_market_cap_impact_in_equity_currency()

        # Calculate price adjustment
        self._calculate_price_adjustment()

        impact_data = {
            'gross_dividend_amount': float(self.dividend.dividend_amount),
            'net_dividend_amount': float(self.net_dividend_amount),
            'eligible_shares': float(self.eligible_outstanding_shares),
            'total_dividend_payout': float(self.total_dividend_marketcap_in_dividend_currency),
            'market_cap_impact': float(self.dividend_impact_in_equity_currency),
            'price_adjustment': float(self.price_adjustment),
            'tax_rate': self.dividend.dividend_tax_rate or 0.0,
            'is_gross_amount': self.dividend.is_gross_dividend_amount
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute dividend payment and adjust equity values"""
        original_state = {
            'market_price': float(self.equity.market_price),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None,
            'shares_outstanding': float(self.equity.shares_outstanding)
        }

        # Apply dividend adjustments
        self._apply_dividend_adjustments()

        # Update dividend model with calculated values
        self.dividend.net_dividend_amount = self.net_dividend_amount
        self.dividend.total_dividend_payout = self.total_dividend_marketcap_in_dividend_currency

        new_state = {
            'market_price': float(self.equity.market_price),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None,
            'shares_outstanding': float(self.equity.shares_outstanding)
        }

        return {
            'original_state': original_state,
            'new_state': new_state,
            'adjustments_applied': {
                'price_adjustment': float(self.price_adjustment),
                'market_cap_reduction': float(self.dividend_impact_in_equity_currency)
            }
        }

    def post_execution_validation(self) -> bool:
        """Validate execution results"""
        errors = []

        # Validate that price was adjusted correctly
        expected_new_price = self.equity.market_price
        if abs(float(expected_new_price) - float(self.equity.market_price)) > 0.01:
            errors.append("Price adjustment validation failed")

        # Validate market cap consistency
        calculated_market_cap = self.equity.market_price * self.equity.shares_outstanding
        if self.equity.market_cap and abs(float(calculated_market_cap) - float(self.equity.market_cap)) > 0.01:
            errors.append("Market cap consistency validation failed")

        # Validate dividend calculations
        if abs(float(self.dividend.total_dividend_payout) - float(
                self.total_dividend_marketcap_in_dividend_currency)) > 0.01:
            errors.append("Dividend payout calculation validation failed")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _calculate_net_dividend_amount(self):
        """Calculate net dividend amount after tax"""
        tax_rate = Decimal('0.0')

        if self.dividend.is_taxable and self.dividend.dividend_tax_rate:
            tax_rate = Decimal(str(self.dividend.dividend_tax_rate))

        dividend_amount = Decimal(str(self.dividend.dividend_amount))

        if self.dividend.is_gross_dividend_amount:
            self.net_dividend_amount = dividend_amount * (Decimal('1.0') - tax_rate)
        else:
            self.net_dividend_amount = dividend_amount

    def _calculate_total_dividend_marketcap_in_dividend_currency(self):
        """calculate_total_dividend_marketcap_in_dividend_currency"""
        self.eligible_outstanding_shares = Decimal(str(self.dividend.eligible_outstanding_shares))
        self.total_dividend_marketcap_in_dividend_currency = self.net_dividend_amount * self.eligible_outstanding_shares

    def _calculate_market_cap_impact_in_equity_currency(self):
        """Calculate market cap impact (reduction due to cash outflow)"""
        # TODO add logic 
        dividend_to_equity_exchange_rate = 1
        self.dividend_impact_in_equity_currency = self.total_dividend_marketcap_in_dividend_currency * dividend_to_equity_exchange_rate

    def _calculate_price_adjustment(self):
        """Calculate price adjustment per share"""
        # Price should be reduced by the net dividend amount
        self.price_adjustment = self.dividend_impact_in_equity_currency / self.equity.shares_outstanding

    def _apply_dividend_adjustments(self):
        """Apply dividend adjustments to equity"""
        # Adjust market price (reduce by dividend amount)
        new_price = self.equity.market_price - self.price_adjustment
        self.equity.market_price = max(Decimal('0.01'), new_price)  # Ensure price doesn't go negative

        # Market cap is automatically recalculated due to the event listener
        # But we can also set it explicitly
        if self.equity.shares_outstanding:
            self.equity.market_cap = self.equity.market_price * self.equity.shares_outstanding
