import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.cash_distribution.ReturnOfCapital import ReturnOfCapital
from Equities.utils.Decorators import performance_monitor
from Equities.utils.Exceptions import ReturnOfCapitalValidationError

logger = logging.getLogger(__name__)


class ReturnOfCapitalExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize return of capital-specific attributes"""
        if not isinstance(self.corporate_action, ReturnOfCapital):
            raise ReturnOfCapitalValidationError("Must provide a ReturnOfCapital instance")

        self.roc = self.corporate_action

        # Initialize calculation results
        self.net_return_amount = None
        self.eligible_outstanding_shares = None
        self.total_return_amount_in_currency = None
        self.return_impact_in_equity_currency = None
        self.price_adjustment = None
        self.cost_basis_adjustment = None

        # Validation and adjustment
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust return of capital dates"""
        # Adjust dates according to calendar
        if self.roc.ex_date:
            self.roc.ex_date = self._adjust_date(
                datetime.combine(self.roc.ex_date, datetime.min.time())
            )

        self.roc.record_date = self._adjust_date(
            datetime.combine(self.roc.record_date, datetime.min.time())
        )

        self.roc.payment_date = self._adjust_date(
            datetime.combine(self.roc.payment_date, datetime.min.time())
        )

        # Validate date sequence
        if self.roc.ex_date and self.roc.record_date:
            if self.roc.ex_date >= self.roc.record_date:
                self.validation_errors.append("Ex-date must be before record date")

        if self.roc.payment_date < self.roc.record_date:
            self.validation_errors.append("Payment date cannot be before record date")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for return of capital execution"""
        errors = []

        # Validate return amount
        if self.roc.return_amount <= 0:
            errors.append("Return amount must be positive")

        # Validate shares
        if self.roc.eligible_outstanding_shares <= 0:
            errors.append("Eligible outstanding shares must be positive")

        # Validate equity state
        if not self.equity.market_price or self.equity.market_price <= 0:
            errors.append("Equity market price must be positive")

        if not self.equity.shares_outstanding or self.equity.shares_outstanding <= 0:
            errors.append("Equity shares outstanding must be positive")

        # Validate currency consistency
        if self.roc.currency != self.equity.currency:
            errors.append("Return of capital currency must match equity currency")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate return of capital financial impacts"""
        # Calculate net return amount after tax
        self._calculate_net_return_amount()

        # Calculate total return amount
        self._calculate_total_return_amount_in_currency()

        # Calculate market cap impact
        self._calculate_market_cap_impact_in_equity_currency()

        # Calculate price adjustment
        self._calculate_price_adjustment()

        # Calculate cost basis adjustment if applicable
        self._calculate_cost_basis_adjustment()

        impact_data = {
            'return_amount': float(self.roc.return_amount),
            'net_return_amount': float(self.net_return_amount),
            'eligible_shares': float(self.eligible_outstanding_shares),
            'total_return_amount': float(self.total_return_amount_in_currency),
            'market_cap_impact': float(self.return_impact_in_equity_currency),
            'price_adjustment': float(self.price_adjustment),
            'cost_basis_adjustment': float(self.cost_basis_adjustment) if self.cost_basis_adjustment else None,
            'tax_rate': self.roc.tax_rate or 0.0,
            'affects_cost_basis': self.roc.affects_cost_basis
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute return of capital payment and adjust equity values"""
        original_state = {
            'market_price': float(self.equity.market_price),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None,
            'shares_outstanding': float(self.equity.shares_outstanding),
            'cost_basis': float(self.equity.cost_basis) if hasattr(self.equity, 'cost_basis') else None
        }

        # Apply return of capital adjustments
        self._apply_return_adjustments()

        # Update return of capital model with calculated values
        self.roc.total_return_amount = self.total_return_amount_in_currency
        if self.roc.affects_cost_basis:
            self.roc.total_cost_basis_reduction = self.cost_basis_adjustment * self.equity.shares_outstanding

        new_state = {
            'market_price': float(self.equity.market_price),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None,
            'shares_outstanding': float(self.equity.shares_outstanding),
            'cost_basis': float(self.equity.cost_basis) if hasattr(self.equity, 'cost_basis') else None
        }

        return {
            'original_state': original_state,
            'new_state': new_state,
            'adjustments_applied': {
                'price_adjustment': float(self.price_adjustment),
                'market_cap_reduction': float(self.return_impact_in_equity_currency),
                'cost_basis_reduction': float(self.cost_basis_adjustment) if self.cost_basis_adjustment else None
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

        # Validate return calculations
        if abs(float(self.roc.total_return_amount) - float(self.total_return_amount_in_currency)) > 0.01:
            errors.append("Return amount calculation validation failed")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _calculate_net_return_amount(self):
        """Calculate net return amount after tax"""
        tax_rate = Decimal('0.0')

        if self.roc.is_taxable and self.roc.tax_rate:
            tax_rate = Decimal(str(self.roc.tax_rate))

        return_amount = Decimal(str(self.roc.return_amount))
        self.net_return_amount = return_amount * (Decimal('1.0') - tax_rate)

    def _calculate_total_return_amount_in_currency(self):
        """Calculate total return amount in currency"""
        self.eligible_outstanding_shares = Decimal(str(self.roc.eligible_outstanding_shares))
        self.total_return_amount_in_currency = self.net_return_amount * self.eligible_outstanding_shares

    def _calculate_market_cap_impact_in_equity_currency(self):
        """Calculate market cap impact (reduction due to cash outflow)"""
        # TODO: Add currency conversion logic if needed
        return_to_equity_exchange_rate = 1
        self.return_impact_in_equity_currency = self.total_return_amount_in_currency * return_to_equity_exchange_rate

    def _calculate_price_adjustment(self):
        """Calculate price adjustment per share"""
        # Price should be reduced by the net return amount
        self.price_adjustment = self.return_impact_in_equity_currency / self.equity.shares_outstanding

    def _calculate_cost_basis_adjustment(self):
        """Calculate cost basis adjustment per share if applicable"""
        if self.roc.affects_cost_basis and self.roc.cost_basis_reduction:
            self.cost_basis_adjustment = Decimal(str(self.roc.cost_basis_reduction))
        else:
            self.cost_basis_adjustment = Decimal('0')

    def _apply_return_adjustments(self):
        """Apply return of capital adjustments to equity"""
        # Adjust market price (reduce by return amount)
        new_price = self.equity.market_price - self.price_adjustment
        self.equity.market_price = max(Decimal('0.01'), new_price)  # Ensure price doesn't go negative

        # Adjust cost basis if applicable
        if hasattr(self.equity, 'cost_basis') and self.roc.affects_cost_basis:
            new_cost_basis = self.equity.cost_basis - self.cost_basis_adjustment
            self.equity.cost_basis = max(Decimal('0'), new_cost_basis)  # Ensure cost basis doesn't go negative

        # Market cap is automatically recalculated due to the event listener
        if self.equity.shares_outstanding:
            self.equity.market_cap = self.equity.market_price * self.equity.shares_outstanding
