import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.rights_and_warrants.Subscription import Subscription
from Equities.utils.Decorators import performance_monitor
from Equities.utils.Exceptions import SubscriptionValidationError

logger = logging.getLogger(__name__)


class SubscriptionExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize subscription-specific attributes"""
        if not isinstance(self.corporate_action, Subscription):
            raise SubscriptionValidationError("Must provide a Subscription instance")

        self.subscription = self.corporate_action

        # Initialize calculation results
        self.shares_to_be_issued = None
        self.proceeds_to_be_raised = None
        self.new_shares_outstanding = None
        self.dilution_factor = None

        # Validation and adjustment
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust subscription dates"""
        self.subscription.offer_date = self._adjust_date(
            datetime.combine(self.subscription.offer_date, datetime.min.time())
        )

        self.subscription.subscription_deadline = self._adjust_date(
            datetime.combine(self.subscription.subscription_deadline, datetime.min.time())
        )

        self.subscription.payment_deadline = self._adjust_date(
            datetime.combine(self.subscription.payment_deadline, datetime.min.time())
        )

        if self.subscription.offer_date >= self.subscription.subscription_deadline:
            self.validation_errors.append("Offer date must be before subscription deadline")

        if self.subscription.subscription_deadline > self.subscription.payment_deadline:
            self.validation_errors.append("Subscription deadline must be before or equal to payment deadline")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for subscription execution"""
        errors = []

        # Validate subscription price
        if self.subscription.subscription_price <= 0:
            errors.append("Subscription price must be positive")

        # Validate subscription ratio
        if self.subscription.subscription_ratio <= 0:
            errors.append("Subscription ratio must be positive")

        # Validate equity state
        if not self.equity.shares_outstanding or self.equity.shares_outstanding <= 0:
            errors.append("Equity shares outstanding must be positive")

        # Validate minimum/maximum subscription limits
        if (self.subscription.minimum_subscription and
                self.subscription.maximum_subscription and
                self.subscription.minimum_subscription > self.subscription.maximum_subscription):
            errors.append("Minimum subscription cannot be greater than maximum subscription")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate subscription financial impacts"""
        # Calculate shares to be issued based on subscription ratio
        self._calculate_shares_to_be_issued()

        # Calculate proceeds to be raised
        self._calculate_proceeds_to_be_raised()

        # Calculate new shares outstanding and dilution
        self._calculate_dilution_impact()

        impact_data = {
            'current_shares_outstanding': float(self.equity.shares_outstanding),
            'shares_to_be_issued': float(self.shares_to_be_issued),
            'new_shares_outstanding': float(self.new_shares_outstanding),
            'proceeds_to_be_raised': float(self.proceeds_to_be_raised),
            'dilution_factor': float(self.dilution_factor),
            'subscription_price': float(self.subscription.subscription_price),
            'subscription_ratio': float(self.subscription.subscription_ratio),
            'minimum_subscription': self.subscription.minimum_subscription or 0,
            'maximum_subscription': self.subscription.maximum_subscription or 0
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute subscription (when shares are actually allotted)"""
        original_state = {
            'shares_outstanding': float(self.equity.shares_outstanding),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None
        }

        # Apply subscription adjustments (only if shares are actually allotted)
        if self.subscription.shares_allotted:
            self._apply_subscription_adjustments()

        new_state = {
            'shares_outstanding': float(self.equity.shares_outstanding),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None
        }

        return {
            'original_state': original_state,
            'new_state': new_state,
            'subscription_details': {
                'shares_applied': self.subscription.shares_applied or 0,
                'shares_allotted': self.subscription.shares_allotted or 0,
                'allotment_ratio': self.subscription.allotment_ratio or 0.0,
                'proceeds_raised': float(
                    self.subscription.shares_allotted * self.subscription.subscription_price) if self.subscription.shares_allotted else 0.0
            },
            'adjustments_applied': {
                'shares_increase': float(new_state['shares_outstanding'] - original_state['shares_outstanding']),
                'dilution_factor': float(self.dilution_factor) if self.subscription.shares_allotted else 0.0
            }
        }

    def post_execution_validation(self) -> bool:
        """Validate execution results"""
        errors = []

        # Validate that shares outstanding increased if subscription was executed
        if self.subscription.shares_allotted and self.subscription.shares_allotted > 0:
            if self.equity.shares_outstanding <= self.subscription.shares_allotted:
                errors.append("Shares outstanding should increase after subscription execution")

        # Validate allotment ratio consistency
        if (self.subscription.shares_applied and self.subscription.shares_allotted and
                self.subscription.allotment_ratio):
            expected_allotment_ratio = self.subscription.shares_allotted / self.subscription.shares_applied
            if abs(expected_allotment_ratio - self.subscription.allotment_ratio) > 0.001:
                errors.append("Allotment ratio validation failed")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _calculate_shares_to_be_issued(self):
        """Calculate shares to be issued based on subscription ratio"""
        self.shares_to_be_issued = Decimal(str(self.equity.shares_outstanding)) * Decimal(
            str(self.subscription.subscription_ratio))

    def _calculate_proceeds_to_be_raised(self):
        """Calculate proceeds to be raised if fully subscribed"""
        self.proceeds_to_be_raised = self.shares_to_be_issued * Decimal(str(self.subscription.subscription_price))

    def _calculate_dilution_impact(self):
        """Calculate dilution impact"""
        self.new_shares_outstanding = Decimal(str(self.equity.shares_outstanding)) + self.shares_to_be_issued
        self.dilution_factor = self.shares_to_be_issued / self.new_shares_outstanding

    def _apply_subscription_adjustments(self):
        """Apply subscription adjustments to equity"""
        if self.subscription.shares_allotted:
            # Increase shares outstanding
            self.equity.shares_outstanding += self.subscription.shares_allotted

            # Market cap increases due to cash injection
            if self.equity.market_cap:
                proceeds = self.subscription.shares_allotted * self.subscription.subscription_price
                self.equity.market_cap += proceeds
