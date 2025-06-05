import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from equity.src.model.corporate_actions.analytics.formulation.CorporateActionExecutorBase import \
    CorporateActionExecutorBase
from equity.src.model.corporate_actions.model.corporate_restructuring.Acquisition import Acquisition
from equity.src.model.equity import Equity
from equity.src.utils.Decorators import performance_monitor
from equity.src.utils.Exceptions import AcquisitionValidationError

logger = logging.getLogger(__name__)


class AcquisitionExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize acquisition-specific attributes"""
        if not isinstance(self.corporate_action, Acquisition):
            raise AcquisitionValidationError("Must provide an Acquisition instance")

        self.acquisition = self.corporate_action
        self.acquirer: Optional[Equity] = None
        self.target = self.equity

        # Initialize calculation results
        self.total_acquisition_value = None
        self.implied_equity_value = None
        self.price_adjustment = None
        self.exchange_ratio_applied = None

        # Fetch acquiring company if specified
        if self.acquisition.acquiring_company_id:
            self.acquirer = self._fetch_equity(self.acquisition.acquiring_company_id)

        # Validate and adjust dates
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust acquisition dates"""
        # Adjust dates according to calendar
        self.acquisition.announcement_date = self._adjust_date(
            datetime.combine(self.acquisition.announcement_date, datetime.min.time())
        )

        self.acquisition.expected_completion_date = self._adjust_date(
            datetime.combine(self.acquisition.expected_completion_date, datetime.min.time())
        )

        if self.acquisition.completion_date:
            self.acquisition.completion_date = self._adjust_date(
                datetime.combine(self.acquisition.completion_date, datetime.min.time())
            )

        # Validate date sequence
        if self.acquisition.announcement_date >= self.acquisition.expected_completion_date:
            self.validation_errors.append("Announcement date must be before expected completion date")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for acquisition execution"""
        errors = []

        # Validate acquisition price
        if self.acquisition.acquisition_price <= 0:
            errors.append("Acquisition price must be positive")

        # Validate equity state
        if not self.target.market_price or self.target.market_price <= 0:
            errors.append("Target equity market price must be positive")

        if not self.target.shares_outstanding or self.target.shares_outstanding <= 0:
            errors.append("Target shares outstanding must be positive")

        # Validate acquirer if specified
        if self.acquirer:
            if not self.acquirer.market_price or self.acquirer.market_price <= 0:
                errors.append("Acquirer market price must be positive")

        # Validate method-specific requirements
        if self.acquisition.acquisition_method == 'STOCK' and not self.acquisition.exchange_ratio:
            errors.append("Exchange ratio must be specified for stock acquisitions")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate acquisition financial impacts"""
        # Calculate total acquisition value
        self._calculate_total_acquisition_value()

        # Calculate implied equity value
        self._calculate_implied_equity_value()

        # Calculate price adjustment
        self._calculate_price_adjustment()

        # Calculate exchange ratio if stock acquisition
        if self.acquisition.acquisition_method == 'STOCK':
            self._calculate_exchange_ratio()

        impact_data = {
            'acquisition_price': float(self.acquisition.acquisition_price),
            'total_acquisition_value': float(self.total_acquisition_value),
            'implied_equity_value': float(self.implied_equity_value),
            'premium_over_market': float(
                self.acquisition.premium_over_market) if self.acquisition.premium_over_market else None,
            'acquisition_method': self.acquisition.acquisition_method,
            'exchange_ratio': float(self.exchange_ratio_applied) if self.exchange_ratio_applied else None,
            'price_adjustment': float(self.price_adjustment) if self.price_adjustment else None,
            'is_friendly': self.acquisition.is_friendly,
            'acquirer_id': self.acquirer.id if self.acquirer else None
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute the acquisition and adjust equity values"""
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

        # Apply acquisition adjustments
        self._apply_acquisition_adjustments()

        # Update acquisition model with calculated values
        self.acquisition.total_acquisition_value = self.total_acquisition_value
        self.acquisition.implied_equity_value = self.implied_equity_value
        if self.exchange_ratio_applied:
            self.acquisition.exchange_ratio = self.exchange_ratio_applied

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
                'price_adjustment': float(self.price_adjustment) if self.price_adjustment else None,
                'exchange_ratio': float(self.exchange_ratio_applied) if self.exchange_ratio_applied else None,
                'acquisition_completed': self.acquisition.is_completed
            }
        }

    def post_execution_validation(self) -> bool:
        """Validate execution results"""
        errors = []

        # For cash acquisitions, validate price adjustment
        if self.acquisition.acquisition_method == 'CASH':
            if abs(float(self.target.market_price) - float(self.acquisition.acquisition_price)) > 0.01:
                errors.append("Price adjustment validation failed for cash acquisition")

        # For stock acquisitions, validate exchange ratio
        if self.acquisition.acquisition_method == 'STOCK' and self.acquirer:
            calculated_ratio = float(self.target.market_price) / float(self.acquirer.market_price)
            if abs(calculated_ratio - float(self.exchange_ratio_applied)) > 0.01:
                errors.append("Exchange ratio validation failed")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _calculate_total_acquisition_value(self):
        """Calculate total acquisition value based on method"""
        if self.acquisition.acquisition_method == 'CASH':
            self.total_acquisition_value = Decimal(
                str(self.acquisition.acquisition_price)) * self.target.shares_outstanding
        elif self.acquisition.acquisition_method == 'STOCK' and self.acquirer:
            self.total_acquisition_value = Decimal(str(self.acquirer.market_price)) * Decimal(
                str(self.acquisition.exchange_ratio)) * self.target.shares_outstanding
        else:
            # For mixed acquisitions, implement appropriate logic
            pass

    def _calculate_implied_equity_value(self):
        """Calculate implied equity value from acquisition terms"""
        self.implied_equity_value = self.total_acquisition_value

        # Calculate premium if not already set
        if not self.acquisition.premium_over_market:
            market_value = self.target.market_price * self.target.shares_outstanding
            self.acquisition.premium_over_market = float(
                (self.implied_equity_value - market_value) / market_value
            )

    def _calculate_price_adjustment(self):
        """Calculate price adjustment for target"""
        if self.acquisition.acquisition_method == 'CASH':
            self.price_adjustment = Decimal(str(self.acquisition.acquisition_price)) - self.target.market_price
        else:
            # For stock acquisitions, price adjustment is handled via exchange ratio
            self.price_adjustment = None

    def _calculate_exchange_ratio(self):
        """Calculate exchange ratio for stock acquisitions"""
        if self.acquirer and self.acquisition.acquisition_method == 'STOCK':
            if not self.acquisition.exchange_ratio:
                self.exchange_ratio_applied = self.target.market_price / self.acquirer.market_price
            else:
                self.exchange_ratio_applied = Decimal(str(self.acquisition.exchange_ratio))

    def _apply_acquisition_adjustments(self):
        """Apply acquisition adjustments to equities"""
        if self.acquisition.acquisition_method == 'CASH':
            # For cash acquisitions, set target price to acquisition price
            self.target.market_price = Decimal(str(self.acquisition.acquisition_price))
            self.target.market_cap = self.target.market_price * self.target.shares_outstanding
            self.acquisition.mark_completed()
        elif self.acquisition.acquisition_method == 'STOCK' and self.acquirer:
            # For stock acquisitions, handle via exchange ratio
            # In a real implementation, you would also handle share conversion here
            self.acquisition.mark_completed()
