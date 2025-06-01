import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.cash_distribution.SpecialDividend import SpecialDividend
from Equities.utils.Decorators import performance_monitor
from Equities.utils.Exceptions import SpecialDividendValidationError

logger = logging.getLogger(__name__)


class SpecialDividendExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize special dividend-specific attributes"""
        if not isinstance(self.corporate_action, SpecialDividend):
            raise SpecialDividendValidationError("Must provide a SpecialDividend instance")

        self.special_dividend = self.corporate_action

        # Initialize calculation results
        self.net_special_dividend_amount = None
        self.eligible_outstanding_shares = None
        self.special_dividend_marketcap_in_ca_currency = None
        self.dividend_impact_in_equity_currency = None
        self.price_adjustment = None

        # Validation and adjustment
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust special dividend dates"""
        # Adjust dates according to calendar
        if self.special_dividend.ex_dividend_date:
            self.special_dividend.ex_dividend_date = self._adjust_date(
                datetime.combine(self.special_dividend.ex_dividend_date, datetime.min.time())
            )

        self.special_dividend.record_date = self._adjust_date(
            datetime.combine(self.special_dividend.record_date, datetime.min.time())
        )

        self.special_dividend.payment_date = self._adjust_date(
            datetime.combine(self.special_dividend.payment_date, datetime.min.time())
        )

        # Validate date sequence
        if self.special_dividend.ex_dividend_date and self.special_dividend.record_date:
            if self.special_dividend.ex_dividend_date >= self.special_dividend.record_date:
                self.validation_errors.append("Ex-dividend date must be before record date")

        if self.special_dividend.payment_date < self.special_dividend.record_date:
            self.validation_errors.append("Payment date cannot be before record date")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for special dividend execution"""
        errors = []

        # Validate dividend amount
        if self.special_dividend.special_dividend_amount <= 0:
            errors.append("Special dividend amount must be positive")

        # Validate shares
        if self.special_dividend.eligible_outstanding_shares <= 0:
            errors.append("Eligible outstanding shares must be positive")

        # Validate equity state
        if not self.equity.market_price or self.equity.market_price <= 0:
            errors.append("Equity market price must be positive")

        if not self.equity.shares_outstanding or self.equity.shares_outstanding <= 0:
            errors.append("Equity shares outstanding must be positive")

        # Validate currency consistency
        if self.special_dividend.currency != self.equity.currency:
            errors.append("Special dividend currency must match equity currency")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate special dividend financial impacts"""
        # Calculate net dividend amount after tax/withholding
        self._calculate_net_special_dividend_amount()

        # Calculate total dividend payout
        self._calculate_total_special_dividend_marketcap_in_dividend_currency()

        # Calculate market cap impact
        self._calculate_market_cap_impact_in_equity_currency()

        # Calculate price adjustment
        self._calculate_price_adjustment()

        impact_data = {
            'gross_special_dividend_amount': float(self.special_dividend.special_dividend_amount),
            'net_special_dividend_amount': float(self.net_special_dividend_amount),
            'eligible_shares': float(self.eligible_outstanding_shares),
            'special_dividend_marketcap_in_ca_currency': float(self.special_dividend_marketcap_in_ca_currency),
            'market_cap_impact': float(self.dividend_impact_in_equity_currency),
            'price_adjustment': float(self.price_adjustment),
            'tax_rate': self.special_dividend.dividend_tax_rate or 0.0,
            'is_gross_amount': self.special_dividend.is_gross_dividend_amount
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute special dividend payment and adjust equity values"""
        original_state = {
            'market_price': float(self.equity.market_price),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None,
            'shares_outstanding': float(self.equity.shares_outstanding)
        }

        # Apply dividend adjustments
        self._apply_special_dividend_adjustments()

        # Update special dividend model with calculated values
        self.special_dividend.net_special_dividend_amount = self.net_special_dividend_amount
        self.special_dividend.special_dividend_marketcap_in_dividend_currency = self.special_dividend_marketcap_in_ca_currency

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
        expected_new_price = self.equity.market_price - self.price_adjustment
        if abs(float(expected_new_price) - float(self.equity.market_price)) > 0.01:
            errors.append("Price adjustment validation failed")

        # Validate market cap consistency
        calculated_market_cap = self.equity.market_price * self.equity.shares_outstanding
        if self.equity.market_cap and abs(float(calculated_market_cap) - float(self.equity.market_cap)) > 0.01:
            errors.append("Market cap consistency validation failed")

        # Validate dividend calculations
        if abs(float(self.special_dividend.total_special_dividend_payout) - float(
                self.special_dividend_marketcap_in_ca_currency)) > 0.01:
            errors.append("Special dividend payout calculation validation failed")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _calculate_net_special_dividend_amount(self):
        """Calculate net special dividend amount after tax"""
        tax_rate = Decimal('0.0')

        if self.special_dividend.is_taxable and self.special_dividend.dividend_tax_rate:
            tax_rate = Decimal(str(self.special_dividend.dividend_tax_rate))

        dividend_amount = Decimal(str(self.special_dividend.special_dividend_amount))

        if self.special_dividend.is_gross_dividend_amount:
            self.net_special_dividend_amount = dividend_amount * (Decimal('1.0') - tax_rate)
        else:
            self.net_special_dividend_amount = dividend_amount

    def _calculate_total_special_dividend_marketcap_in_dividend_currency(self):
        """Calculate total special dividend marketcap_in_dividend_currency"""
        self.eligible_outstanding_shares = Decimal(str(self.special_dividend.eligible_outstanding_shares))
        self.special_dividend_marketcap_in_ca_currency = self.net_special_dividend_amount * self.eligible_outstanding_shares

    def _calculate_market_cap_impact_in_equity_currency(self):
        """Calculate market cap impact (reduction due to cash outflow)"""
        # TODO: Add currency conversion logic
        dividend_to_equity_exchange_rate = 1
        self.dividend_impact_in_equity_currency = (
                self.special_dividend_marketcap_in_ca_currency * dividend_to_equity_exchange_rate
        )

    def _calculate_price_adjustment(self):
        """Calculate price adjustment per share"""
        # Price should be reduced by the net special dividend amount
        self.price_adjustment = self.dividend_impact_in_equity_currency / self.equity.shares_outstanding

    def _apply_special_dividend_adjustments(self):
        """Apply special dividend adjustments to equity"""
        # Adjust market price (reduce by dividend amount)
        new_price = self.equity.market_price - self.price_adjustment
        self.equity.market_price = max(Decimal('0.01'), new_price)  # Ensure price doesn't go negative

        # Market cap is automatically recalculated due to the event listener
        if self.equity.shares_outstanding:
            self.equity.market_cap = self.equity.market_price * self.equity.shares_outstanding
