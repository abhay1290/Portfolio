import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from equity.src.model.corporate_actions.analytics.formulation.CorporateActionExecutorBase import \
    CorporateActionExecutorBase
from equity.src.model.corporate_actions.model.delisting_and_reorganization.Delisting import Delisting
from equity.src.utils.Decorators import performance_monitor
from equity.src.utils.Exceptions import DelistingValidationError

logger = logging.getLogger(__name__)


class DelistingExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize delisting-specific attributes"""
        if not isinstance(self.corporate_action, Delisting):
            raise DelistingValidationError("Must provide a Delisting instance")

        self.delisting = self.corporate_action
        self.equity = self._fetch_equity(self.delisting.equity_id)

        # Initialize calculation results
        self.pre_delisting_value = None
        self.post_delisting_value = None

        # Validate and adjust dates
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust delisting dates"""
        # Adjust dates according to calendar
        self.delisting.announcement_date = self._adjust_date(
            datetime.combine(self.delisting.announcement_date, datetime.min.time())
        )
        self.delisting.effective_date = self._adjust_date(
            datetime.combine(self.delisting.effective_date, datetime.min.time())
        )

        # Validate date sequence
        if self.delisting.announcement_date > self.delisting.effective_date:
            self.validation_errors.append("Announcement date cannot be after effective date")

        if self.delisting.effective_date > self.delisting.execution_date:
            self.validation_errors.append("Effective date cannot be after execution date")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for delisting execution"""
        errors = []

        # Validate equity state
        if not self.equity.market_price or self.equity.market_price <= 0:
            errors.append("Equity market price must be positive")

        if not self.equity.shares_outstanding or self.equity.shares_outstanding <= 0:
            errors.append("Shares outstanding must be positive")

        # Validate delisting reason
        if not self.delisting.reason:
            errors.append("Delisting reason must be specified")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate delisting financial impacts"""
        self.pre_delisting_value = self.equity.market_price * self.equity.shares_outstanding

        if self.delisting.final_price is not None:
            self.post_delisting_value = Decimal(str(self.delisting.final_price)) * self.equity.shares_outstanding
        else:
            self.post_delisting_value = Decimal('0')

        impact_data = {
            'pre_delisting_value': float(self.pre_delisting_value),
            'post_delisting_value': float(self.post_delisting_value),
            'final_price': float(self.delisting.final_price) if self.delisting.final_price is not None else None,
            'reason': self.delisting.reason,
            'is_voluntary': self.delisting.is_voluntary,
            'is_trading_suspended': self.delisting.is_trading_suspended
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute the delisting and adjust equity values"""
        original_state = {
            'equity': {
                'market_price': float(self.equity.market_price),
                'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None,
                'shares_outstanding': float(self.equity.shares_outstanding)
            }
        }

        # Apply delisting adjustments
        self._apply_delisting_adjustments()

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
                'trading_suspended': self.delisting.is_trading_suspended
            }
        }

    def post_execution_validation(self) -> bool:
        """Validate execution results"""
        errors = []

        if self.delisting.is_trading_suspended and not self.equity.is_trading_suspended:
            errors.append("Trading should be suspended after delisting")

        if self.delisting.final_price is not None and float(self.equity.market_price) != float(
                self.delisting.final_price):
            errors.append("Final price adjustment validation failed")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _apply_delisting_adjustments(self):
        """Apply delisting adjustments to equity"""
        if self.delisting.final_price is not None:
            self.equity.market_price = Decimal(str(self.delisting.final_price))
            self.equity.market_cap = self.equity.market_price * self.equity.shares_outstanding
        else:
            self.equity.market_price = Decimal('0')
            self.equity.market_cap = Decimal('0')

        self.delisting.mark_trading_suspended(self.delisting.effective_date)
        self.delisting.mark_completed()
