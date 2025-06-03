import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from equity.src.model.corporate_actions.analytics.formulation.CorporateActionExecutorBase import \
    CorporateActionExecutorBase
from equity.src.model.corporate_actions.model.rights_and_warrants.WarrentExercise import WarrantExercise
from equity.src.utils.Decorators import performance_monitor
from equity.src.utils.Exceptions import WarrantValidationError

logger = logging.getLogger(__name__)


class WarrantExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize warrant-specific attributes"""
        if not isinstance(self.corporate_action, WarrantExercise):
            raise WarrantValidationError("Must provide a Warrant instance")

        self.warrant = self.corporate_action

        # Initialize calculation results
        self.warrants_outstanding = None
        self.theoretical_ex_warrant_price = None
        self.theoretical_warrant_value = None
        self.max_new_shares = None
        self.proceeds_if_fully_exercised = None

        # Validation and adjustment
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust warrant dates"""
        self.warrant.ex_warrant_date = self._adjust_date(
            datetime.combine(self.warrant.ex_warrant_date, datetime.min.time())
        )

        self.warrant.exercise_deadline = self._adjust_date(
            datetime.combine(self.warrant.exercise_deadline, datetime.min.time())
        )

        if self.warrant.warrant_trading_start:
            self.warrant.warrant_trading_start = self._adjust_date(
                datetime.combine(self.warrant.warrant_trading_start, datetime.min.time())
            )

        if self.warrant.warrant_trading_end:
            self.warrant.warrant_trading_end = self._adjust_date(
                datetime.combine(self.warrant.warrant_trading_end, datetime.min.time())
            )

        if self.warrant.ex_warrant_date >= self.warrant.exercise_deadline:
            self.validation_errors.append("Ex-warrant date must be before exercise deadline")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for warrant execution"""
        errors = []

        # Validate exercise price
        if self.warrant.exercise_price <= 0:
            errors.append("Exercise price must be positive")

        # Validate ratios
        if self.warrant.warrant_ratio <= 0:
            errors.append("Warrant ratio must be positive")

        if self.warrant.exercise_ratio <= 0:
            errors.append("Exercise ratio must be positive")

        # Validate equity state
        if not self.equity.market_price or self.equity.market_price <= 0:
            errors.append("Equity market price must be positive")

        if not self.equity.shares_outstanding or self.equity.shares_outstanding <= 0:
            errors.append("Equity shares outstanding must be positive")

        # Validate that exercise price is below market price (for in-the-money warrants)
        if self.warrant.exercise_price >= self.equity.market_price:
            errors.append("Exercise price should be below market price for warrants to have intrinsic value")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate warrant financial impacts"""
        # Calculate warrants outstanding
        self._calculate_warrants_outstanding()

        # Calculate theoretical values
        self._calculate_theoretical_values()

        # Calculate maximum new shares if fully exercised
        self._calculate_max_new_shares()

        # Calculate proceeds if fully exercised
        self._calculate_proceeds_if_fully_exercised()

        impact_data = {
            'warrants_outstanding': float(self.warrants_outstanding),
            'theoretical_ex_warrant_price': float(self.theoretical_ex_warrant_price),
            'theoretical_warrant_value': float(self.theoretical_warrant_value),
            'max_new_shares_if_fully_exercised': float(self.max_new_shares),
            'proceeds_if_fully_exercised': float(self.proceeds_if_fully_exercised),
            'exercise_price': float(self.warrant.exercise_price),
            'current_market_price': float(self.equity.market_price),
            'warrant_ratio': float(self.warrant.warrant_ratio),
            'exercise_ratio': float(self.warrant.exercise_ratio)
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute warrant exercise and adjust equity values"""
        original_state = {
            'market_price': float(self.equity.market_price),
            'shares_outstanding': float(self.equity.shares_outstanding),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None
        }

        # Apply warrant adjustments (ex-warrant adjustment)
        self._apply_warrant_adjustments()

        # Update warrant model with calculated values
        self.warrant.theoretical_warrant_value = self.theoretical_warrant_value

        new_state = {
            'market_price': float(self.equity.market_price),
            'shares_outstanding': float(self.equity.shares_outstanding),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None
        }

        return {
            'original_state': original_state,
            'new_state': new_state,
            'warrant_details': {
                'warrants_outstanding': float(self.warrants_outstanding),
                'theoretical_warrant_value': float(self.theoretical_warrant_value),
                'max_dilution_if_fully_exercised': float(
                    self.max_new_shares / self.equity.shares_outstanding) if self.equity.shares_outstanding > 0 else 0.0
            },
            'adjustments_applied': {
                'price_adjustment_to_ex_warrant': float(original_state['market_price'] - new_state['market_price'])
            }
        }

    def post_execution_validation(self) -> bool:
        """Validate execution results"""
        errors = []

        # Validate that price was adjusted to theoretical ex-warrant price
        if abs(float(self.equity.market_price) - float(self.theoretical_ex_warrant_price)) > 0.01:
            errors.append("Price adjustment to ex-warrant price validation failed")

        # Validate that warrant value is positive (assuming exercise price < market price)
        if self.theoretical_warrant_value <= 0:
            errors.append("Theoretical warrant value should be positive")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _calculate_warrants_outstanding(self):
        """Calculate total warrants outstanding"""
        self.warrants_outstanding = Decimal(str(self.equity.shares_outstanding)) * Decimal(
            str(self.warrant.warrant_ratio))

    def _calculate_theoretical_values(self):
        """Calculate theoretical ex-warrant price and warrant value"""
        # Formula: Ex-warrant price = (Market Price + (Exercise Price / Warrant Ratio)) / (1 + (1 / Warrant Ratio))
        market_price = Decimal(str(self.equity.market_price))
        exercise_price = Decimal(str(self.warrant.exercise_price))
        warrant_ratio = Decimal(str(self.warrant.warrant_ratio))

        numerator = market_price + (exercise_price / warrant_ratio)
        denominator = Decimal('1') + (Decimal('1') / warrant_ratio)

        self.theoretical_ex_warrant_price = numerator / denominator
        self.theoretical_warrant_value = market_price - self.theoretical_ex_warrant_price

    def _calculate_max_new_shares(self):
        """Calculate maximum new shares if fully exercised"""
        self.max_new_shares = self.warrants_outstanding * Decimal(str(self.warrant.exercise_ratio))

    def _calculate_proceeds_if_fully_exercised(self):
        """Calculate proceeds if fully exercised"""
        self.proceeds_if_fully_exercised = self.max_new_shares * Decimal(str(self.warrant.exercise_price))

    def _apply_warrant_adjustments(self):
        """Apply warrant adjustments to equity (ex-warrant adjustment)"""
        # Adjust market price to theoretical ex-warrant price
        self.equity.market_price = self.theoretical_ex_warrant_price

        # Market cap is adjusted accordingly
        if self.equity.market_cap:
            self.equity.market_cap = self.equity.market_price * self.equity.shares_outstanding
