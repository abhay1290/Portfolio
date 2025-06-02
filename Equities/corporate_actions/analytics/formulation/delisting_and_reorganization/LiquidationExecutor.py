import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.delisting_and_reorganization.Liquidation import Liquidation
from Equities.utils.Decorators import performance_monitor
from Equities.utils.Exceptions import LiquidationValidationError

logger = logging.getLogger(__name__)


class LiquidationExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize liquidation-specific attributes"""
        if not isinstance(self.corporate_action, Liquidation):
            raise LiquidationValidationError("Must provide a Liquidation instance")

        self.liquidation = self.corporate_action
        self.equity = self._fetch_equity(self.liquidation.equity_id)

        # Initialize calculation results
        self.pre_liquidation_value = None
        self.post_liquidation_value = None
        self.liquidation_proceeds = None

        # Validate and adjust dates
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust liquidation dates"""
        self.liquidation.announcement_date = self._adjust_date(
            datetime.combine(self.liquidation.announcement_date, datetime.min.time())
        )
        self.liquidation.completion_date = self._adjust_date(
            datetime.combine(self.liquidation.completion_date, datetime.min.time())
        )

        # Validate date sequence
        if self.liquidation.announcement_date > self.liquidation.completion_date:
            self.validation_errors.append("Announcement date cannot be after completion date")

        if self.liquidation.completion_date > self.liquidation.execution_date:
            self.validation_errors.append("Completion date cannot be after execution date")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for liquidation execution"""
        errors = []

        # Validate equity state
        if not self.equity.market_price or self.equity.market_price <= 0:
            errors.append("Equity market price must be positive")

        if not self.equity.shares_outstanding or self.equity.shares_outstanding <= 0:
            errors.append("Shares outstanding must be positive")

        # Validate liquidation proceeds if provided
        if (self.liquidation.proceeds_per_share is not None and
                self.liquidation.proceeds_per_share < 0):
            errors.append("Liquidation proceeds cannot be negative")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate liquidation financial impacts"""
        self.pre_liquidation_value = self.equity.market_price * self.equity.shares_outstanding

        if self.liquidation.proceeds_per_share is not None:
            self.liquidation_proceeds = Decimal(
                str(self.liquidation.proceeds_per_share)) * self.equity.shares_outstanding
            self.post_liquidation_value = self.liquidation_proceeds
        else:
            self.post_liquidation_value = Decimal('0')

        impact_data = {
            'pre_liquidation_value': float(self.pre_liquidation_value),
            'post_liquidation_value': float(self.post_liquidation_value),
            'liquidation_proceeds': float(self.liquidation_proceeds) if self.liquidation_proceeds is not None else None,
            'proceeds_per_share': float(
                self.liquidation.proceeds_per_share) if self.liquidation.proceeds_per_share is not None else None,
            'liquidation_type': self.liquidation.liquidation_type,
            'is_trading_suspended': self.liquidation.is_trading_suspended
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute the liquidation and adjust equity values"""
        original_state = {
            'equity': {
                'market_price': float(self.equity.market_price),
                'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None,
                'shares_outstanding': float(self.equity.shares_outstanding)
            }
        }

        # Apply liquidation adjustments
        self._apply_liquidation_adjustments()

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
                'trading_suspended': self.liquidation.is_trading_suspended
            }
        }

    def post_execution_validation(self) -> bool:
        """Validate execution results"""
        errors = []

        if not self.liquidation.is_trading_suspended:
            errors.append("Trading should be suspended after liquidation")

        if (self.liquidation.proceeds_per_share is not None and
                float(self.equity.market_price) != float(self.liquidation.proceeds_per_share)):
            errors.append("Liquidation proceeds adjustment validation failed")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _apply_liquidation_adjustments(self):
        """Apply liquidation adjustments to equity"""
        if self.liquidation.proceeds_per_share is not None:
            self.equity.market_price = Decimal(str(self.liquidation.proceeds_per_share))
            self.equity.market_cap = self.equity.market_price * self.equity.shares_outstanding
        else:
            self.equity.market_price = Decimal('0')
            self.equity.market_cap = Decimal('0')

        self.liquidation.mark_trading_suspended(self.liquidation.completion_date)
        self.liquidation.mark_completed()
