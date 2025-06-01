import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.corporate_restructuring.ExchangeOffer import ExchangeOffer
from Equities.model.Equity import Equity
from Equities.utils.Decorators import performance_monitor
from Equities.utils.Exceptions import ExchangeOfferValidationError

logger = logging.getLogger(__name__)


class ExchangeOfferExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize exchange offer-specific attributes"""
        if not isinstance(self.corporate_action, ExchangeOffer):
            raise ExchangeOfferValidationError("Must provide an ExchangeOffer instance")

        self.exchange_offer = self.corporate_action
        self.original_security = self.equity
        self.new_security: Optional[Equity] = None

        # Initialize calculation results
        self.implied_value_per_share = None
        self.implied_premium = None
        self.participation_rate = None

        # Fetch new security
        self.new_security = self._fetch_equity(self.exchange_offer.new_security_id)

        # Validate and adjust dates
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust exchange offer dates"""
        # Adjust dates according to calendar
        self.exchange_offer.offer_date = self._adjust_date(
            datetime.combine(self.exchange_offer.offer_date, datetime.min.time())
        )

        self.exchange_offer.expiration_date = self._adjust_date(
            datetime.combine(self.exchange_offer.expiration_date, datetime.min.time())
        )

        if self.exchange_offer.settlement_date:
            self.exchange_offer.settlement_date = self._adjust_date(
                datetime.combine(self.exchange_offer.settlement_date, datetime.min.time())
            )

        # Validate date sequence
        if self.exchange_offer.offer_date >= self.exchange_offer.expiration_date:
            self.validation_errors.append("Offer date must be before expiration date")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for exchange offer execution"""
        errors = []

        # Validate securities
        if not self.original_security.market_price or self.original_security.market_price <= 0:
            errors.append("Original security market price must be positive")

        if not self.new_security.market_price or self.new_security.market_price <= 0:
            errors.append("New security market price must be positive")

        # Validate exchange ratio
        if self.exchange_offer.exchange_ratio <= 0:
            errors.append("Exchange ratio must be positive")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate exchange offer financial impacts"""
        # Calculate implied value per share
        self._calculate_implied_value()

        # Calculate implied premium
        self._calculate_implied_premium()

        impact_data = {
            'exchange_ratio': float(self.exchange_offer.exchange_ratio),
            'cash_component': float(self.exchange_offer.cash_component) if self.exchange_offer.cash_component else None,
            'implied_value_per_share': float(self.implied_value_per_share),
            'implied_premium': float(self.implied_premium),
            'original_security_price': float(self.original_security.market_price),
            'new_security_price': float(self.new_security.market_price),
            'is_voluntary': self.exchange_offer.is_voluntary,
            'fractional_shares_handling': self.exchange_offer.fractional_shares_handling
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute the exchange offer and adjust security values"""
        original_state = {
            'original_security': {
                'market_price': float(self.original_security.market_price),
                'shares_outstanding': float(self.original_security.shares_outstanding)
            },
            'new_security': {
                'market_price': float(self.new_security.market_price),
                'shares_outstanding': float(self.new_security.shares_outstanding)
            }
        }

        # Apply exchange offer adjustments
        self._apply_exchange_adjustments()

        # Update exchange offer model with calculated values
        self.exchange_offer.implied_premium = self.implied_premium

        new_state = {
            'original_security': {
                'market_price': float(self.original_security.market_price),
                'shares_outstanding': float(self.original_security.shares_outstanding)
            },
            'new_security': {
                'market_price': float(self.new_security.market_price),
                'shares_outstanding': float(self.new_security.shares_outstanding)
            }
        }

        return {
            'original_state': original_state,
            'new_state': new_state,
            'adjustments_applied': {
                'implied_premium': float(self.implied_premium),
                'exchange_completed': self.exchange_offer.is_completed
            }
        }

    def post_execution_validation(self) -> bool:
        """Validate execution results"""
        errors = []

        # Validate implied premium calculation
        if abs(float(self.implied_premium)) > 5.0:  # Arbitrary large premium threshold
            errors.append("Implied premium validation failed - unusually high value")
        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _calculate_implied_value(self):
        """Calculate implied value per share from exchange terms"""
        self.implied_value_per_share = (
                Decimal(str(self.exchange_offer.exchange_ratio)) * self.new_security.market_price
        )
        if self.exchange_offer.cash_component:
            self.implied_value_per_share += Decimal(str(self.exchange_offer.cash_component))

    def _calculate_implied_premium(self):
        """Calculate implied premium over original security price"""
        original_price = self.original_security.market_price
        self.implied_premium = float(
            (self.implied_value_per_share - original_price) / original_price
        )
        self.exchange_offer.implied_premium = self.implied_premium

    def _apply_exchange_adjustments(self):
        """Apply exchange offer adjustments to securities"""
        # In a real implementation, this would handle the actual exchange of securities
        # For now, we'll just mark the offer as completed
        self.exchange_offer.mark_completed()
