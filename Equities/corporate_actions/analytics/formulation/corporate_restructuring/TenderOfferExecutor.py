import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.corporate_restructuring.TenderOffer import TenderOffer
from Equities.utils.Decorators import performance_monitor
from Equities.utils.Exceptions import TenderOfferValidationError

logger = logging.getLogger(__name__)


class TenderOfferExecutor(CorporateActionExecutorBase):
    def _initialize_executor(self):
        """Initialize tender offer-specific attributes"""
        if not isinstance(self.corporate_action, TenderOffer):
            raise TenderOfferValidationError("Must provide a TenderOffer instance")

        self.tender_offer = self.corporate_action
        self.target = self.equity

        # Initialize calculation results
        self.total_consideration = None
        self.premium_over_market = None
        self.expected_acceptance = None

        # Validate and adjust dates
        self._adjust_and_validate_dates()

    def _adjust_and_validate_dates(self):
        """Validate and adjust tender offer dates"""
        # Adjust dates according to calendar
        self.tender_offer.offer_date = self._adjust_date(
            datetime.combine(self.tender_offer.offer_date, datetime.min.time())
        )

        self.tender_offer.expiration_date = self._adjust_date(
            datetime.combine(self.tender_offer.expiration_date, datetime.min.time())
        )

        if self.tender_offer.withdrawal_deadline:
            self.tender_offer.withdrawal_deadline = self._adjust_date(
                datetime.combine(self.tender_offer.withdrawal_deadline, datetime.min.time())
            )

        if self.tender_offer.proration_date:
            self.tender_offer.proration_date = self._adjust_date(
                datetime.combine(self.tender_offer.proration_date, datetime.min.time())
            )

        # Validate date sequence
        if self.tender_offer.offer_date >= self.tender_offer.expiration_date:
            self.validation_errors.append("Offer date must be before expiration date")

        if (self.tender_offer.withdrawal_deadline and
                self.tender_offer.withdrawal_deadline >= self.tender_offer.expiration_date):
            self.validation_errors.append("Withdrawal deadline must be before expiration date")

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for tender offer execution"""
        errors = []

        # Validate target equity
        if not self.target.market_price or self.target.market_price <= 0:
            errors.append("Target equity market price must be positive")

        if not self.target.shares_outstanding or self.target.shares_outstanding <= 0:
            errors.append("Target shares outstanding must be positive")

        # Validate offer price
        if self.tender_offer.offer_price <= self.target.market_price:
            errors.append("Offer price should typically be above market price")

        # Validate share amounts
        if (self.tender_offer.minimum_shares_sought and
                self.tender_offer.maximum_shares_sought and
                self.tender_offer.minimum_shares_sought > self.tender_offer.maximum_shares_sought):
            errors.append("Minimum shares sought cannot exceed maximum shares sought")

        # Validate dates
        if self.validation_errors:
            errors.extend(self.validation_errors)

        self.validation_errors = errors
        return len(errors) == 0

    @performance_monitor
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate tender offer financial impacts"""
        # Calculate premium over market
        self._calculate_premium()

        # Calculate expected acceptance
        self._calculate_expected_acceptance()

        # Calculate total consideration
        self._calculate_total_consideration()

        impact_data = {
            'offer_price': float(self.tender_offer.offer_price),
            'premium_over_market': float(self.premium_over_market),
            'minimum_shares_sought': self.tender_offer.minimum_shares_sought,
            'maximum_shares_sought': self.tender_offer.maximum_shares_sought,
            'expected_acceptance': self.expected_acceptance,
            'total_consideration': float(self.total_consideration),
            'is_conditional': self.tender_offer.is_conditional,
            'minimum_tender_condition': self.tender_offer.minimum_tender_condition,
            'is_going_private': self.tender_offer.is_going_private
        }

        return impact_data

    def execute_action(self) -> Dict[str, Any]:
        """Execute the tender offer and adjust equity values"""
        original_state = {
            'target': {
                'market_price': float(self.target.market_price),
                'shares_outstanding': float(self.target.shares_outstanding),
                'market_cap': float(self.target.market_cap) if self.target.market_cap else None
            }
        }

        # Apply tender offer adjustments
        self._apply_tender_adjustments()

        # Update tender offer model with calculated values
        self.tender_offer.premium_over_market = self.premium_over_market
        self.tender_offer.total_consideration = self.total_consideration

        new_state = {
            'target': {
                'market_price': float(self.target.market_price),
                'shares_outstanding': float(self.target.shares_outstanding),
                'market_cap': float(self.target.market_cap) if self.target.market_cap else None
            }
        }

        return {
            'original_state': original_state,
            'new_state': new_state,
            'adjustments_applied': {
                'shares_accepted': self.tender_offer.shares_accepted,
                'final_price': float(self.tender_offer.final_price) if self.tender_offer.final_price else None,
                'tender_completed': self.tender_offer.is_completed
            }
        }

    def post_execution_validation(self) -> bool:
        """Validate execution results"""
        errors = []

        # Validate premium calculation
        if self.premium_over_market < 0:
            errors.append("Premium over market should typically be positive")

        # Validate total consideration
        if self.total_consideration <= 0:
            errors.append("Total consideration must be positive")

        if errors:
            logger.error(f"Post-execution validation failed: {errors}")
            return False

        return True

    def _calculate_premium(self):
        """Calculate premium over market price"""
        self.tender_offer.calculate_premium(float(self.target.market_price))
        self.premium_over_market = self.tender_offer.premium_over_market

    def _calculate_expected_acceptance(self):
        """Calculate expected shares acceptance"""
        if self.tender_offer.maximum_shares_sought:
            self.expected_acceptance = min(
                self.target.shares_outstanding,
                self.tender_offer.maximum_shares_sought
            )
        else:
            self.expected_acceptance = self.target.shares_outstanding

    def _calculate_total_consideration(self):
        """Calculate total consideration based on expected acceptance"""
        self.total_consideration = Decimal(str(self.tender_offer.offer_price)) * self.expected_acceptance
        self.tender_offer.total_consideration = self.total_consideration

    def _apply_tender_adjustments(self):
        """Apply tender offer adjustments to equity"""
        # In a real implementation, this would handle the actual tender processing
        # For now, we'll simulate acceptance and mark as completed
        shares_accepted = self.expected_acceptance

        # If going private, all shares would be accepted
        if self.tender_offer.is_going_private:
            shares_accepted = self.target.shares_outstanding

        self.tender_offer.mark_completed(
            actual_completion_date=datetime.now().date(),
            shares_tendered=self.target.shares_outstanding,  # Assume all shares tendered
            shares_accepted=shares_accepted
        )

        # Update final price (could differ from offer price in some cases)
        self.tender_offer.final_price = self.tender_offer.offer_price
