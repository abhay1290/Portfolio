import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from equity.src.model.corporate_actions.analytics.formulation.CorporateActionExecutorBase import \
    CorporateActionExecutorBase
from equity.src.model.corporate_actions.model.cash_distribution.Distribution import Distribution
from equity.src.utils.Decorators import performance_monitor
from equity.src.utils.Exceptions import DistributionValidationError

logger = logging.getLogger(__name__)


class DistributionExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize distribution-specific attributes"""
        if not isinstance(self.corporate_action, Distribution):
            raise DistributionValidationError("Must provide a Distribution instance")

        self.distribution = self.corporate_action

        # Initialize calculation results
        self.net_distribution_amount = None
        self.eligible_outstanding_shares = None
        self.total_distribution_payout = None
        self.distribution_impact_in_equity_currency = None
        self.price_adjustment = None

        # Validation and adjustment
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust distribution dates"""
        # Adjust dates according to calendar
        if self.distribution.ex_distribution_date:
            self.distribution.ex_distribution_date = self._adjust_date(
                datetime.combine(self.distribution.ex_distribution_date, datetime.min.time())
            )

        self.distribution.record_date = self._adjust_date(
            datetime.combine(self.distribution.record_date, datetime.min.time())
        )

        self.distribution.payment_date = self._adjust_date(
            datetime.combine(self.distribution.payment_date, datetime.min.time())
        )

        # Validate date sequence
        if self.distribution.ex_distribution_date and self.distribution.record_date:
            if self.distribution.ex_distribution_date >= self.distribution.record_date:
                self.validation_errors.append("Ex-distribution date must be before record date")

        if self.distribution.payment_date < self.distribution.record_date:
            self.validation_errors.append("Payment date cannot be before record date")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for distribution execution"""
        errors = []

        # Validate distribution amount
        if self.distribution.distribution_amount <= 0:
            errors.append("Distribution amount must be positive")

        # Validate shares
        if self.distribution.eligible_outstanding_shares <= 0:
            errors.append("Eligible outstanding shares must be positive")

        # Validate equity state
        if not self.equity.market_price or self.equity.market_price <= 0:
            errors.append("Equity market price must be positive")

        if not self.equity.shares_outstanding or self.equity.shares_outstanding <= 0:
            errors.append("Equity shares outstanding must be positive")

        # Validate currency consistency
        if self.distribution.currency != self.equity.currency:
            errors.append("Distribution currency must match equity currency")

        # Validate distribution type
        if not self.distribution.distribution_type:
            errors.append("Distribution type must be specified")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    def _get_currency_conversion_rate(self) -> Decimal:
        """Get conversion rate from distribution currency to equity currency"""
        # TODO: Implement actual currency conversion logic
        return Decimal('1.0')

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate distribution financial impacts"""
        # Calculate net distribution amount after tax
        self._calculate_net_distribution_amount()

        # Calculate total distribution payout
        self._calculate_total_distribution_payout()

        # Calculate market cap impact
        self._calculate_market_cap_impact_in_equity_currency()

        # Calculate price adjustment
        self._calculate_price_adjustment()

        impact_data = {
            'gross_distribution_amount': float(self.distribution.distribution_amount),
            'net_distribution_amount': float(self.net_distribution_amount),
            'eligible_shares': float(self.eligible_outstanding_shares),
            'total_distribution_payout': float(self.total_distribution_payout),
            'market_cap_impact': float(self.distribution_impact_in_equity_currency),
            'price_adjustment': float(self.price_adjustment),
            'tax_rate': self.distribution.distribution_tax_rate or 0.0,
            'is_gross_amount': self.distribution.is_gross_distribution_amount,
            'distribution_type': self.distribution.distribution_type,
            'taxable_amount': float(self.distribution.taxable_amount) if self.distribution.taxable_amount else None,
            'non_taxable_amount': float(
                self.distribution.non_taxable_amount) if self.distribution.non_taxable_amount else None
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute distribution payment and adjust equity values"""
        original_state = {
            'market_price': float(self.equity.market_price),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None,
            'shares_outstanding': float(self.equity.shares_outstanding)
        }

        # Apply distribution adjustments
        self._apply_distribution_adjustments()

        # Update distribution model with calculated values
        self.distribution.net_distribution_amount = self.net_distribution_amount
        self.distribution.total_distribution_payout = self.total_distribution_payout

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
                'market_cap_reduction': float(self.distribution_impact_in_equity_currency)
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

        # Validate distribution calculations
        if abs(float(self.distribution.total_distribution_payout) - float(
                self.total_distribution_payout)) > 0.01:
            errors.append("Distribution payout calculation validation failed")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _calculate_net_distribution_amount(self):
        """Calculate net distribution amount after tax"""
        tax_rate = Decimal('0.0')

        if self.distribution.is_taxable and self.distribution.distribution_tax_rate:
            tax_rate = Decimal(str(self.distribution.distribution_tax_rate))

        distribution_amount = Decimal(str(self.distribution.distribution_amount))

        if self.distribution.is_gross_distribution_amount:
            self.net_distribution_amount = distribution_amount * (Decimal('1.0') - tax_rate)
        else:
            self.net_distribution_amount = distribution_amount

        # Handle taxable/non-taxable amounts if specified
        if self.distribution.taxable_amount is not None:
            self.distribution.taxable_amount = Decimal(str(self.distribution.taxable_amount))
        if self.distribution.non_taxable_amount is not None:
            self.distribution.non_taxable_amount = Decimal(str(self.distribution.non_taxable_amount))

    def _calculate_total_distribution_payout(self):
        """Calculate total distribution payout"""
        self.eligible_outstanding_shares = Decimal(str(self.distribution.eligible_outstanding_shares))
        self.total_distribution_payout = self.net_distribution_amount * self.eligible_outstanding_shares

    def _calculate_market_cap_impact_in_equity_currency(self):
        """Calculate market cap impact (reduction due to cash outflow)"""
        conversion_rate = self._get_currency_conversion_rate()
        self.distribution_impact_in_equity_currency = self.total_distribution_payout * conversion_rate

    def _calculate_price_adjustment(self):
        """Calculate price adjustment per share"""
        self.price_adjustment = self.distribution_impact_in_equity_currency / self.equity.shares_outstanding

    def _apply_distribution_adjustments(self):
        """Apply distribution adjustments to equity"""
        new_price = self.equity.market_price - self.price_adjustment
        self.equity.market_price = max(Decimal('0.01'), new_price)

        if self.equity.shares_outstanding:
            self.equity.market_cap = self.equity.market_price * self.equity.shares_outstanding
