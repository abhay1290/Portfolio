import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from equity.src.model import Equity
from equity.src.model.corporate_actions.analytics.formulation.CorporateActionExecutorBase import \
    CorporateActionExecutorBase
from equity.src.model.corporate_actions.enums.MergerTypeEnum import MergerTypeEnum
from equity.src.model.corporate_actions.model.corporate_restructuring.Merger import Merger
from equity.src.utils.Decorators import performance_monitor
from equity.src.utils.Exceptions import MergerValidationError

logger = logging.getLogger(__name__)


class MergerExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize merger-specific attributes"""
        if not isinstance(self.corporate_action, Merger):
            raise MergerValidationError("Must provide a Merger instance")

        self.merger = self.corporate_action
        self.target = self.equity
        self.acquirer: Optional[Equity] = None

        # Initialize calculation results
        self.implied_premium = None
        self.total_consideration_value = None
        self.synergy_estimate = None

        # Fetch acquiring company if specified
        if self.merger.acquiring_company_id:
            self.acquirer = self._fetch_equity(self.merger.acquiring_company_id)

        # Validate and adjust dates
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust merger dates"""
        # Adjust dates according to calendar
        self.merger.announcement_date = self._adjust_date(
            datetime.combine(self.merger.announcement_date, datetime.min.time())
        )

        if self.merger.shareholder_approval_date:
            self.merger.shareholder_approval_date = self._adjust_date(
                datetime.combine(self.merger.shareholder_approval_date, datetime.min.time())
            )

        self.merger.effective_date = self._adjust_date(
            datetime.combine(self.merger.effective_date, datetime.min.time())
        )

        # Validate date sequence
        if self.merger.announcement_date >= self.merger.effective_date:
            self.validation_errors.append("Announcement date must be before effective date")

        if (self.merger.shareholder_approval_date and
                self.merger.shareholder_approval_date >= self.merger.effective_date):
            self.validation_errors.append("Shareholder approval date must be before effective date")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for merger execution"""
        errors = []

        # Validate target equity
        if not self.target.market_price or self.target.market_price <= 0:
            errors.append("Target equity market price must be positive")

        if not self.target.shares_outstanding or self.target.shares_outstanding <= 0:
            errors.append("Target shares outstanding must be positive")

        # Validate acquirer if specified
        if self.acquirer and not self.acquirer.market_price:
            errors.append("Acquirer market price must be positive")

        # Validate consideration
        if not self.merger.cash_consideration and not self.merger.stock_consideration_ratio:
            errors.append("Merger must have either cash or stock consideration")

        if (self.merger.stock_consideration_ratio and
                not self.merger.acquiring_company_id):
            errors.append("Stock consideration requires acquiring company")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate merger financial impacts"""
        # Calculate total consideration value
        self._calculate_total_consideration()

        # Calculate implied premium
        self._calculate_implied_premium()

        # Calculate synergy estimate if not provided
        if not self.merger.synergy_estimate:
            self._estimate_synergies()

        impact_data = {
            'merger_type': self.merger.merger_type.value,
            'cash_consideration': float(self.merger.cash_consideration) if self.merger.cash_consideration else None,
            'stock_consideration_ratio': float(
                self.merger.stock_consideration_ratio) if self.merger.stock_consideration_ratio else None,
            'total_consideration_value': float(self.total_consideration_value),
            'implied_premium': float(self.implied_premium),
            'synergy_estimate': float(self.synergy_estimate) if self.synergy_estimate else None,
            'is_tax_free': self.merger.is_tax_free_reorganization,
            'acquirer_id': self.acquirer.id if self.acquirer else None
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute the merger and adjust equity values"""
        original_state = {
            'target': {
                'market_price': float(self.target.market_price),
                'market_cap': float(self.target.market_cap) if self.target.market_cap else None,
                'shares_outstanding': float(self.target.shares_outstanding)
            },
            'acquirer': {
                'market_price': float(self.acquirer.market_price) if self.acquirer else None,
                'market_cap': float(self.acquirer.market_cap) if self.acquirer and self.acquirer.market_cap else None,
                'shares_outstanding': float(self.acquirer.shares_outstanding) if self.acquirer else None
            } if self.acquirer else None
        }

        # Apply merger adjustments
        self._apply_merger_adjustments()

        # Update merger model with calculated values
        self.merger.total_consideration_value = self.total_consideration_value
        self.merger.implied_premium = self.implied_premium
        if self.synergy_estimate:
            self.merger.synergy_estimate = self.synergy_estimate

        new_state = {
            'target': {
                'market_price': float(self.target.market_price),
                'market_cap': float(self.target.market_cap) if self.target.market_cap else None,
                'shares_outstanding': float(self.target.shares_outstanding)
            },
            'acquirer': {
                'market_price': float(self.acquirer.market_price) if self.acquirer else None,
                'market_cap': float(self.acquirer.market_cap) if self.acquirer and self.acquirer.market_cap else None,
                'shares_outstanding': float(self.acquirer.shares_outstanding) if self.acquirer else None
            } if self.acquirer else None
        }

        return {
            'original_state': original_state,
            'new_state': new_state,
            'adjustments_applied': {
                'total_consideration': float(self.total_consideration_value),
                'merger_completed': self.merger.is_completed
            }
        }

    def post_execution_validation(self) -> bool:
        """Validate execution results"""
        errors = []

        # Validate consideration calculation
        if self.total_consideration_value <= 0:
            errors.append("Total consideration validation failed - must be positive")

        # Validate premium calculation
        if abs(float(self.implied_premium)) > 5.0:  # Arbitrary large premium threshold
            errors.append("Implied premium validation failed - unusually high value")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _calculate_total_consideration(self):
        """Calculate total consideration value"""
        acquirer_price = self.acquirer.market_price if self.acquirer else None
        self.total_consideration_value = self.merger.calculate_total_consideration(acquirer_price)

    def _calculate_implied_premium(self):
        """Calculate implied premium over target's market cap"""
        target_market_cap = float(self.target.market_price * self.target.shares_outstanding)
        self.merger.calculate_implied_premium(target_market_cap)
        self.implied_premium = self.merger.implied_premium

    def _estimate_synergies(self):
        """Estimate synergies based on merger type and companies"""
        # Simple estimation - in reality this would be more complex
        if self.merger.merger_type == MergerTypeEnum.CASH:
            self.synergy_estimate = self.total_consideration_value * Decimal('0.10')  # 10% of deal value
        elif self.merger.merger_type == MergerTypeEnum.STOCK:
            self.synergy_estimate = self.total_consideration_value * Decimal('0.07')
        else:
            self.synergy_estimate = self.total_consideration_value * Decimal('0.05')

    def _apply_merger_adjustments(self):
        """Apply merger adjustments to equities"""
        # In a real implementation, this would handle the actual merger
        # For now, we'll just mark the merger as completed
        self.merger.mark_completed()
