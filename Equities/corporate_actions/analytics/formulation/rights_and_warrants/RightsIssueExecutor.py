import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.rights_and_warrants.RightsIssue import RightsIssue
from Equities.utils.Decorators import performance_monitor
from Equities.utils.Exceptions import RightsIssueValidationError

logger = logging.getLogger(__name__)


class RightsIssueExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize rights issue-specific attributes"""
        if not isinstance(self.corporate_action, RightsIssue):
            raise RightsIssueValidationError("Must provide a RightsIssue instance")

        self.rights_issue = self.corporate_action

        # Initialize calculation results
        self.rights_distributed = None
        self.theoretical_ex_rights_price = None
        self.theoretical_rights_value = None
        self.max_new_shares = None
        self.proceeds_if_fully_subscribed = None

        # Validation and adjustment
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust rights issue dates"""
        self.rights_issue.ex_rights_date = self._adjust_date(
            datetime.combine(self.rights_issue.ex_rights_date, datetime.min.time())
        )

        self.rights_issue.subscription_deadline = self._adjust_date(
            datetime.combine(self.rights_issue.subscription_deadline, datetime.min.time())
        )

        if self.rights_issue.rights_trading_start:
            self.rights_issue.rights_trading_start = self._adjust_date(
                datetime.combine(self.rights_issue.rights_trading_start, datetime.min.time())
            )

        if self.rights_issue.rights_trading_end:
            self.rights_issue.rights_trading_end = self._adjust_date(
                datetime.combine(self.rights_issue.rights_trading_end, datetime.min.time())
            )

        if self.rights_issue.ex_rights_date >= self.rights_issue.subscription_deadline:
            self.validation_errors.append("Ex-rights date must be before subscription deadline")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for rights issue execution"""
        errors = []

        # Validate subscription price
        if self.rights_issue.subscription_price <= 0:
            errors.append("Subscription price must be positive")

        # Validate ratios
        if self.rights_issue.rights_ratio <= 0:
            errors.append("Rights ratio must be positive")

        if self.rights_issue.subscription_ratio <= 0:
            errors.append("Subscription ratio must be positive")

        # Validate equity state
        if not self.equity.market_price or self.equity.market_price <= 0:
            errors.append("Equity market price must be positive")

        if not self.equity.shares_outstanding or self.equity.shares_outstanding <= 0:
            errors.append("Equity shares outstanding must be positive")

        # Validate that subscription price is below market price
        if self.rights_issue.subscription_price >= self.equity.market_price:
            errors.append("Subscription price should be below market price for rights to have value")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate rights issue financial impacts"""
        # Calculate rights distributed
        self._calculate_rights_distributed()

        # Calculate theoretical values
        self._calculate_theoretical_values()

        # Calculate maximum new shares if fully subscribed
        self._calculate_max_new_shares()

        # Calculate proceeds if fully subscribed
        self._calculate_proceeds_if_fully_subscribed()

        impact_data = {
            'rights_distributed': float(self.rights_distributed),
            'theoretical_ex_rights_price': float(self.theoretical_ex_rights_price),
            'theoretical_rights_value': float(self.theoretical_rights_value),
            'max_new_shares_if_fully_subscribed': float(self.max_new_shares),
            'proceeds_if_fully_subscribed': float(self.proceeds_if_fully_subscribed),
            'subscription_price': float(self.rights_issue.subscription_price),
            'current_market_price': float(self.equity.market_price),
            'rights_ratio': float(self.rights_issue.rights_ratio),
            'subscription_ratio': float(self.rights_issue.subscription_ratio)
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute rights issue and adjust equity values"""
        original_state = {
            'market_price': float(self.equity.market_price),
            'shares_outstanding': float(self.equity.shares_outstanding),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None
        }

        # Apply rights issue adjustments (ex-rights adjustment)
        self._apply_rights_issue_adjustments()

        # Update rights issue model with calculated values
        self.rights_issue.theoretical_rights_value = self.theoretical_rights_value

        new_state = {
            'market_price': float(self.equity.market_price),
            'shares_outstanding': float(self.equity.shares_outstanding),
            'market_cap': float(self.equity.market_cap) if self.equity.market_cap else None
        }

        return {
            'original_state': original_state,
            'new_state': new_state,
            'rights_details': {
                'rights_distributed': float(self.rights_distributed),
                'theoretical_rights_value': float(self.theoretical_rights_value),
                'max_dilution_if_fully_subscribed': float(
                    self.max_new_shares / self.equity.shares_outstanding) if self.equity.shares_outstanding > 0 else 0.0
            },
            'adjustments_applied': {
                'price_adjustment_to_ex_rights': float(original_state['market_price'] - new_state['market_price'])
            }
        }

    def post_execution_validation(self) -> bool:
        """Validate execution results"""
        errors = []

        # Validate that price was adjusted to theoretical ex-rights price
        if abs(float(self.equity.market_price) - float(self.theoretical_ex_rights_price)) > 0.01:
            errors.append("Price adjustment to ex-rights price validation failed")

        # Validate that rights value is positive (assuming subscription price < market price)
        if self.theoretical_rights_value <= 0:
            errors.append("Theoretical rights value should be positive")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _calculate_rights_distributed(self):
        """Calculate total rights distributed"""
        self.rights_distributed = Decimal(str(self.equity.shares_outstanding)) * Decimal(
            str(self.rights_issue.rights_ratio))

    def _calculate_theoretical_values(self):
        """Calculate theoretical ex-rights price and rights value"""
        # Formula: Ex-rights price = (Market Price + (Subscription Price / Rights Ratio)) / (1 + (1 / Rights Ratio))
        market_price = Decimal(str(self.equity.market_price))
        subscription_price = Decimal(str(self.rights_issue.subscription_price))
        rights_ratio = Decimal(str(self.rights_issue.rights_ratio))

        numerator = market_price + (subscription_price / rights_ratio)
        denominator = Decimal('1') + (Decimal('1') / rights_ratio)

        self.theoretical_ex_rights_price = numerator / denominator
        self.theoretical_rights_value = market_price - self.theoretical_ex_rights_price

    def _calculate_max_new_shares(self):
        """Calculate maximum new shares if fully subscribed"""
        self.max_new_shares = self.rights_distributed * Decimal(str(self.rights_issue.subscription_ratio))

    def _calculate_proceeds_if_fully_subscribed(self):
        """Calculate proceeds if fully subscribed"""
        self.proceeds_if_fully_subscribed = self.max_new_shares * Decimal(str(self.rights_issue.subscription_price))

    def _apply_rights_issue_adjustments(self):
        """Apply rights issue adjustments to equity (ex-rights adjustment)"""
        # Adjust market price to theoretical ex-rights price
        self.equity.market_price = self.theoretical_ex_rights_price

        # Market cap is adjusted accordingly
        if self.equity.market_cap:
            self.equity.market_cap = self.equity.market_price * self.equity.shares_outstanding
