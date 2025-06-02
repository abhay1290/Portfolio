import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.delisting_and_reorganization.Bankruptcy import Bankruptcy
from Equities.utils.Decorators import performance_monitor
from Equities.utils.Exceptions import BankruptcyValidationError

logger = logging.getLogger(__name__)


class BankruptcyExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize bankruptcy-specific attributes"""
        if not isinstance(self.corporate_action, Bankruptcy):
            raise BankruptcyValidationError("Must provide a Bankruptcy instance")

        self.bankruptcy = self.corporate_action
        self.equity = self._fetch_equity(self.bankruptcy.equity_id)

        # Initialize calculation results
        self.pre_bankruptcy_value = None
        self.post_bankruptcy_value = None
        self.recovery_value = None

        # Validate and adjust dates
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust bankruptcy dates"""
        # Adjust dates according to calendar
        self.bankruptcy.filing_date = self._adjust_date(
            datetime.combine(self.bankruptcy.filing_date, datetime.min.time())
        )

        if self.bankruptcy.court_approval_date:
            self.bankruptcy.court_approval_date = self._adjust_date(
                datetime.combine(self.bankruptcy.court_approval_date, datetime.min.time())
            )

        if self.bankruptcy.plan_effective_date:
            self.bankruptcy.plan_effective_date = self._adjust_date(
                datetime.combine(self.bankruptcy.plan_effective_date, datetime.min.time())
            )

        # Validate date sequence
        if self.bankruptcy.filing_date > self.bankruptcy.execution_date:
            self.validation_errors.append("Filing date cannot be after execution date")

        if (self.bankruptcy.court_approval_date and
                self.bankruptcy.filing_date > self.bankruptcy.court_approval_date):
            self.validation_errors.append("Filing date cannot be after court approval date")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for bankruptcy execution"""
        errors = []

        # Validate equity state
        if not self.equity.market_price or self.equity.market_price <= 0:
            errors.append("Equity market price must be positive")

        if not self.equity.shares_outstanding or self.equity.shares_outstanding <= 0:
            errors.append("Shares outstanding must be positive")

        # Validate recovery rate if provided
        if (self.bankruptcy.estimated_recovery_rate is not None and
                (self.bankruptcy.estimated_recovery_rate < 0 or self.bankruptcy.estimated_recovery_rate > 1)):
            errors.append("Recovery rate must be between 0 and 1")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate bankruptcy financial impacts"""
        # Calculate pre-bankruptcy value
        self.pre_bankruptcy_value = self.equity.market_price * self.equity.shares_outstanding

        # Calculate recovery value if recovery rate is provided
        if self.bankruptcy.estimated_recovery_rate is not None:
            self.recovery_value = self.pre_bankruptcy_value * Decimal(str(self.bankruptcy.estimated_recovery_rate))
            self.post_bankruptcy_value = self.recovery_value
        else:
            self.post_bankruptcy_value = Decimal('0')

        impact_data = {
            'pre_bankruptcy_value': float(self.pre_bankruptcy_value),
            'post_bankruptcy_value': float(self.post_bankruptcy_value),
            'recovery_value': float(self.recovery_value) if self.recovery_value is not None else None,
            'recovery_rate': float(
                self.bankruptcy.estimated_recovery_rate) if self.bankruptcy.estimated_recovery_rate is not None else None,
            'bankruptcy_type': self.bankruptcy.bankruptcy_type,
            'is_trading_suspended': self.bankruptcy.is_trading_suspended
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute the bankruptcy and adjust equity values"""
        original_state = {
            'equity': {
                'market_price': float(self.equity.market_price),
                'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None,
                'shares_outstanding': float(self.equity.shares_outstanding)
            }
        }

        # Apply bankruptcy adjustments
        self._apply_bankruptcy_adjustments()

        new_state = {
            'equity': {
                'market_price': float(self.equity.market_price),
                'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None,
                'shares_outstanding': float(self.equity.shares_outstanding)
            }
        }

        return {
            'original_state': original_state,
            'new_state': new_state,
            'adjustments_applied': {
                'market_price_adjustment': float(
                    self.equity.market_price - Decimal(original_state['equity']['market_price'])),
                'trading_suspended': self.bankruptcy.is_trading_suspended
            }
        }

    def post_execution_validation(self) -> bool:
        """Validate execution results"""
        errors = []

        # For Chapter 7 bankruptcies, validate price went to zero
        if self.bankruptcy.bankruptcy_type == 'Chapter 7' and self.equity.market_price != 0:
            errors.append("Price should be zero for Chapter 7 bankruptcy")

        # For Chapter 11 bankruptcies, validate price adjustment if recovery rate was provided
        if (self.bankruptcy.bankruptcy_type == 'Chapter 11' and
                self.bankruptcy.estimated_recovery_rate is not None and
                abs(float(self.equity.market_price) - float(self.post_bankruptcy_value) / float(
                    self.equity.shares_outstanding)) > 0.01):
            errors.append("Price adjustment validation failed for bankruptcy")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _apply_bankruptcy_adjustments(self):
        """Apply bankruptcy adjustments to equity"""
        if self.bankruptcy.bankruptcy_type == 'Chapter 7':
            # For Chapter 7 (liquidation), set price to zero
            self.equity.market_price = Decimal('0')
            self.equity.market_cap = Decimal('0')
            self.bankruptcy.mark_trading_suspended(self.bankruptcy.execution_date)
        elif self.bankruptcy.bankruptcy_type == 'Chapter 11' and self.bankruptcy.estimated_recovery_rate is not None:
            # For Chapter 11 (reorganization), adjust price based on recovery rate
            new_price = self.post_bankruptcy_value / self.equity.shares_outstanding
            self.equity.market_price = new_price
            self.equity.market_cap = self.post_bankruptcy_value

        self.bankruptcy.mark_completed()
