import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.delisting_and_reorganization.Reorganization import Reorganization
from Equities.utils.Decorators import performance_monitor
from Equities.utils.Exceptions import ReorganizationValidationError

logger = logging.getLogger(__name__)


class ReorganizationExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize reorganization-specific attributes"""
        if not isinstance(self.corporate_action, Reorganization):
            raise ReorganizationValidationError("Must provide a Reorganization instance")

        self.reorganization = self.corporate_action
        self.equity = self._fetch_equity(self.reorganization.equity_id)

        # Initialize calculation results
        self.pre_reorganization_value = None
        self.post_reorganization_value = None
        self.conversion_ratio = None

        # Validate and adjust dates
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust reorganization dates"""
        self.reorganization.announcement_date = self._adjust_date(
            datetime.combine(self.reorganization.announcement_date, datetime.min.time())
        )
        self.reorganization.effective_date = self._adjust_date(
            datetime.combine(self.reorganization.effective_date, datetime.min.time())
        )

        # Validate date sequence
        if self.reorganization.announcement_date > self.reorganization.effective_date:
            self.validation_errors.append("Announcement date cannot be after effective date")

        if self.reorganization.effective_date > self.reorganization.execution_date:
            self.validation_errors.append("Effective date cannot be after execution date")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for reorganization execution"""
        errors = []

        # Validate equity state
        if not self.equity.market_price or self.equity.market_price <= 0:
            errors.append("Equity market price must be positive")

        if not self.equity.shares_outstanding or self.equity.shares_outstanding <= 0:
            errors.append("Shares outstanding must be positive")

        # Validate reorganization parameters
        if not self.reorganization.reorganization_type:
            errors.append("Reorganization type must be specified")

        if (self.reorganization.conversion_ratio is not None and
                self.reorganization.conversion_ratio <= 0):
            errors.append("Conversion ratio must be positive")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate reorganization financial impacts"""
        self.pre_reorganization_value = self.equity.market_price * self.equity.shares_outstanding

        if self.reorganization.conversion_ratio is not None:
            self.post_reorganization_value = self.pre_reorganization_value * Decimal(
                str(self.reorganization.conversion_ratio))
            self.conversion_ratio = Decimal(str(self.reorganization.conversion_ratio))
        else:
            self.post_reorganization_value = self.pre_reorganization_value

        impact_data = {
            'pre_reorganization_value': float(self.pre_reorganization_value),
            'post_reorganization_value': float(self.post_reorganization_value),
            'conversion_ratio': float(self.conversion_ratio) if self.conversion_ratio is not None else None,
            'reorganization_type': self.reorganization.reorganization_type,
            'is_trading_suspended': self.reorganization.is_trading_suspended
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute the reorganization and adjust equity values"""
        original_state = {
            'equity': {
                'market_price': float(self.equity.market_price),
                'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None,
                'shares_outstanding': float(self.equity.shares_outstanding)
            }
        }

        # Apply reorganization adjustments
        self._apply_reorganization_adjustments()

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
                'shares_outstanding_adjustment': float(
                    self.equity.shares_outstanding - Decimal(original_state['equity']['shares_outstanding'])),
                'trading_suspended': self.reorganization.is_trading_suspended
            }
        }

    def post_execution_validation(self) -> bool:
        """Validate execution results"""
        errors = []

        if (self.reorganization.conversion_ratio is not None and
                abs(float(self.equity.market_cap) - float(self.post_reorganization_value)) > 0.01):
            errors.append("Market cap adjustment validation failed for reorganization")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _apply_reorganization_adjustments(self):
        """Apply reorganization adjustments to equity"""
        if self.reorganization.conversion_ratio is not None:
            new_shares = self.equity.shares_outstanding * Decimal(str(self.reorganization.conversion_ratio))
            new_price = (self.equity.market_price * self.equity.shares_outstanding) / new_shares

            self.equity.shares_outstanding = new_shares
            self.equity.market_price = new_price
            self.equity.market_cap = new_price * new_shares

        if self.reorganization.is_trading_suspended:
            self.reorganization.mark_trading_suspended(self.reorganization.effective_date)

        self.reorganization.mark_completed()
