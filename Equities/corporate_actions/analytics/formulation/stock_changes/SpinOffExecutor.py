import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.stock_changes.SpinOff import SpinOff
from Equities.utils.Decorators import performance_monitor
from Equities.utils.Exceptions import SpinOffValidationError

logger = logging.getLogger(__name__)


class SpinOffExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize spin-off-specific attributes"""
        if not isinstance(self.corporate_action, SpinOff):
            raise SpinOffValidationError("Must provide a SpinOff instance")

        self.spinoff = self.corporate_action

        # Initialize calculation results
        self.spinoff_shares_distributed = None
        self.parent_cost_basis_adjustment = None
        self.spinoff_cost_basis = None
        self.parent_market_value_adjustment = None

        # Validation and adjustment
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust spin-off dates"""
        self.spinoff.ex_date = self._adjust_date(
            datetime.combine(self.spinoff.ex_date, datetime.min.time())
        )

        self.spinoff.distribution_date = self._adjust_date(
            datetime.combine(self.spinoff.distribution_date, datetime.min.time())
        )

        if self.spinoff.ex_date > self.spinoff.distribution_date:
            self.validation_errors.append("Ex-date must be before or equal to distribution date")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for spin-off execution"""
        errors = []

        # Validate distribution ratio
        if self.spinoff.distribution_ratio <= 0:
            errors.append("Distribution ratio must be positive")

        # Validate cost basis allocations
        if self.spinoff.parent_cost_basis_allocation and self.spinoff.spinoff_cost_basis_allocation:
            total_allocation = self.spinoff.parent_cost_basis_allocation + self.spinoff.spinoff_cost_basis_allocation
            if abs(total_allocation - 1.0) > 0.001:
                errors.append("Parent and spinoff cost basis allocations must sum to 1.0")

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
        """Calculate spin-off financial impacts"""
        # Calculate spinoff shares to be distributed
        self._calculate_spinoff_shares_distributed()

        # Calculate cost basis adjustments
        self._calculate_cost_basis_adjustments()

        # Calculate parent company market value adjustment
        self._calculate_parent_market_value_adjustment()

        impact_data = {
            'parent_shares_outstanding': float(self.equity.shares_outstanding),
            'spinoff_shares_distributed': float(self.spinoff_shares_distributed),
            'distribution_ratio': float(self.spinoff.distribution_ratio),
            'parent_cost_basis_allocation': self.spinoff.parent_cost_basis_allocation or 0.0,
            'spinoff_cost_basis_allocation': self.spinoff.spinoff_cost_basis_allocation or 0.0,
            'spinoff_fair_value': float(self.spinoff.spinoff_fair_value) if self.spinoff.spinoff_fair_value else 0.0,
            'parent_market_value_adjustment': float(
                self.parent_market_value_adjustment) if self.parent_market_value_adjustment else 0.0
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute spin-off and adjust parent company values"""
        original_state = {
            'market_price': float(self.equity.market_price),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None,
            'shares_outstanding': float(self.equity.shares_outstanding)
        }

        # Apply spin-off adjustments
        self._apply_spinoff_adjustments()

        new_state = {
            'market_price': float(self.equity.market_price),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None,
            'shares_outstanding': float(self.equity.shares_outstanding)
        }

        return {
            'original_state': original_state,
            'new_state': new_state,
            'spinoff_details': {
                'spinoff_shares_distributed': float(self.spinoff_shares_distributed),
                'spinoff_total_value': float(
                    self.spinoff.spinoff_fair_value * self.spinoff_shares_distributed) if self.spinoff.spinoff_fair_value else 0.0
            },
            'adjustments_applied': {
                'parent_market_value_reduction': float(
                    self.parent_market_value_adjustment) if self.parent_market_value_adjustment else 0.0
            }
        }

    def post_execution_validation(self) -> bool:
        """Validate execution results"""
        errors = []

        # Validate that parent company value was reduced appropriately
        if self.spinoff.spinoff_fair_value and self.parent_market_value_adjustment:
            expected_reduction = float(self.spinoff.spinoff_fair_value) * float(self.spinoff_shares_distributed)
            actual_reduction = float(self.parent_market_value_adjustment)
            if abs(expected_reduction - actual_reduction) > 0.01:
                errors.append("Parent company value reduction validation failed")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _calculate_spinoff_shares_distributed(self):
        """Calculate total spinoff shares to be distributed"""
        self.spinoff_shares_distributed = Decimal(str(self.equity.shares_outstanding)) * Decimal(
            str(self.spinoff.distribution_ratio))

    def _calculate_cost_basis_adjustments(self):
        """Calculate cost basis adjustments for parent and spinoff"""
        if self.spinoff.parent_cost_basis_allocation:
            original_cost_basis = self.equity.market_price * self.equity.shares_outstanding
            self.parent_cost_basis_adjustment = original_cost_basis * Decimal(
                str(self.spinoff.parent_cost_basis_allocation))
            self.spinoff_cost_basis = original_cost_basis * Decimal(
                str(self.spinoff.spinoff_cost_basis_allocation or 0))

    def _calculate_parent_market_value_adjustment(self):
        """Calculate parent company market value adjustment"""
        if self.spinoff.spinoff_fair_value:
            self.parent_market_value_adjustment = Decimal(
                str(self.spinoff.spinoff_fair_value)) * self.spinoff_shares_distributed

    def _apply_spinoff_adjustments(self):
        """Apply spin-off adjustments to parent equity"""
        # Reduce parent company market value by spinoff value
        if self.parent_market_value_adjustment:
            value_per_share = self.parent_market_value_adjustment / Decimal(str(self.equity.shares_outstanding))
            self.equity.market_price = max(Decimal('0.01'), self.equity.market_price - value_per_share)

        # Market cap is reduced by spinoff value
        if self.equity.market_cap and self.parent_market_value_adjustment:
            self.equity.market_cap = max(Decimal('0.01'), self.equity.market_cap - self.parent_market_value_adjustment)
