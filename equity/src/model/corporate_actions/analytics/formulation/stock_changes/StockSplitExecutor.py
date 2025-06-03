import logging
from datetime import datetime
from typing import Any, Dict

from equity.src.model.corporate_actions.analytics.formulation.CorporateActionExecutorBase import \
    CorporateActionExecutorBase
from equity.src.model.corporate_actions.model.stock_changes.StockSplit import StockSplit
from equity.src.utils.Decorators import performance_monitor
from equity.src.utils.Exceptions import StockSplitValidationError

logger = logging.getLogger(__name__)


class StockSplitExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize stock split-specific attributes"""
        if not isinstance(self.corporate_action, StockSplit):
            raise StockSplitValidationError("Must provide a StockSplit instance")

        self.stock_split = self.corporate_action

        # Initialize calculation results
        self.new_shares_outstanding = None
        self.new_market_price = None
        self.fractional_shares = None
        self.cash_in_lieu_amount = None

        # Validation and adjustment
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust stock split dates"""
        self.stock_split.ex_split_date = self._adjust_date(
            datetime.combine(self.stock_split.ex_split_date, datetime.min.time())
        )

        self.stock_split.effective_date = self._adjust_date(
            datetime.combine(self.stock_split.effective_date, datetime.min.time())
        )

        if self.stock_split.ex_split_date > self.stock_split.effective_date:
            self.validation_errors.append("Ex-split date must be before or equal to effective date")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for stock split execution"""
        errors = []

        # Validate split ratios
        if self.stock_split.split_ratio_from <= 0:
            errors.append("Split ratio from must be positive")

        if self.stock_split.split_ratio_to <= 0:
            errors.append("Split ratio to must be positive")

        if self.stock_split.split_ratio_to <= self.stock_split.split_ratio_from:
            errors.append("Stock split ratio must increase shares (to > from)")

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
        """Calculate stock split financial impacts"""
        # Calculate new share count
        self._calculate_new_shares_outstanding()

        # Calculate new price
        self._calculate_new_market_price()

        # Calculate fractional shares and cash in lieu
        self._calculate_fractional_shares_and_cash()

        impact_data = {
            'old_shares_outstanding': float(self.equity.shares_outstanding),
            'new_shares_outstanding': float(self.new_shares_outstanding),
            'old_market_price': float(self.equity.market_price),
            'new_market_price': float(self.new_market_price),
            'split_multiplier': float(self.stock_split.split_multiplier),
            'fractional_shares': float(self.fractional_shares) if self.fractional_shares else 0.0,
            'cash_in_lieu_total': float(self.cash_in_lieu_amount) if self.cash_in_lieu_amount else 0.0
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute stock split and adjust equity values"""
        original_state = {
            'market_price': float(self.equity.market_price),
            'shares_outstanding': float(self.equity.shares_outstanding),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None
        }

        # Apply stock split adjustments
        self._apply_stock_split_adjustments()

        new_state = {
            'market_price': float(self.equity.market_price),
            'shares_outstanding': float(self.equity.shares_outstanding),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None
        }

        return {
            'original_state': original_state,
            'new_state': new_state,
            'adjustments_applied': {
                'shares_increase': float(new_state['shares_outstanding'] - original_state['shares_outstanding']),
                'price_decrease': float(original_state['market_price'] - new_state['market_price']),
                'cash_in_lieu_paid': float(self.cash_in_lieu_amount) if self.cash_in_lieu_amount else 0.0
            }
        }

    def post_execution_validation(self) -> bool:
        """Validate execution results"""
        errors = []

        # Validate market cap preservation (approximately)
        calculated_market_cap = self.equity.market_price * self.equity.shares_outstanding
        if self.equity.market_cap and abs(float(calculated_market_cap) - float(self.equity.market_cap)) > 0.01:
            errors.append("Market cap preservation validation failed")

        # Validate share count increase
        if self.equity.shares_outstanding <= self.new_shares_outstanding:
            errors.append("Shares outstanding should be increased after stock split")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _calculate_new_shares_outstanding(self):
        """Calculate new shares outstanding after stock split"""
        self.new_shares_outstanding = Decimal(str(self.equity.shares_outstanding)) * Decimal(
            str(self.stock_split.split_multiplier))

    def _calculate_new_market_price(self):
        """Calculate new market price after stock split"""
        self.new_market_price = Decimal(str(self.equity.market_price)) / Decimal(str(self.stock_split.split_multiplier))

    def _calculate_fractional_shares_and_cash(self):
        """Calculate fractional shares and cash in lieu payments"""
        if self.stock_split.cash_in_lieu_rate:
            # For stock splits, fractional shares are typically minimal
            # This is more relevant for odd ratios like 3:2 splits
            pass

    def _apply_stock_split_adjustments(self):
        """Apply stock split adjustments to equity"""
        # Update shares outstanding
        self.equity.shares_outstanding = self.new_shares_outstanding

        # Update market price
        self.equity.market_price = self.new_market_price

        # Market cap should remain approximately the same
        self.equity.market_cap = self.equity.market_price * self.equity.shares_outstanding
