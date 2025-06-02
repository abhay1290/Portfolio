# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Annotated, Optional

from pydantic import AfterValidator, ConfigDict, Field, model_validator
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class SubscriptionRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.SUBSCRIPTION, frozen=True,
                                                 description="Type of corporate action")

    # Subscription Details
    subscription_price: condecimal(max_digits=20, decimal_places=6, gt=0, strict=True) = Field(...,
                                                                                               description="Price per share for the subscription offer")
    subscription_ratio: condecimal(max_digits=10, decimal_places=6, gt=0, strict=True) = Field(...,
                                                                                               description="Ratio of new shares offered per existing share")
    minimum_subscription: Optional[
        Annotated[int, Field(gt=0), AfterValidator(lambda x: None if x == 0 else x)]] = Field(None,
                                                                                              description="Minimum number of shares that can be subscribed")
    maximum_subscription: Optional[
        Annotated[int, Field(gt=0), AfterValidator(lambda x: None if x == 0 else x)]] = Field(None,
                                                                                              description="Maximum number of shares that can be subscribed")

    # Key Dates
    offer_date: date = Field(..., description="Subscription offer date")
    subscription_deadline: date = Field(..., description="Subscription deadline")
    payment_deadline: date = Field(..., description="Payment deadline")
    allotment_date: Optional[date] = Field(None)

    # Subscription Results
    shares_applied: Optional[int] = Field(None, ge=0)
    shares_allotted: Optional[int] = Field(None, ge=0)
    allotment_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Additional Information
    subscription_purpose: Optional[constr(max_length=1000)] = Field(None)
    subscription_notes: Optional[constr(max_length=2000)] = Field(None)

    # Cross-field validations
    @model_validator(mode='after')
    def validate_subscription_limits(self):
        if (self.minimum_subscription is not None and
                self.maximum_subscription is not None and
                self.minimum_subscription > self.maximum_subscription):
            raise ValueError("Minimum subscription cannot be greater than maximum subscription")

    def validate_dates_chronology(dates: dict):
        """Helper function to validate date chronology"""
        if dates['offer_date'] > dates['subscription_deadline']:
            raise ValueError("Offer date must be before subscription deadline")
        if dates['subscription_deadline'] > dates['payment_deadline']:
            raise ValueError("Subscription deadline must be before payment deadline")
        if dates['allotment_date'] and dates['payment_deadline'] > dates['allotment_date']:
            raise ValueError("Payment deadline must be before allotment date")

    @model_validator(mode='after')
    def validate_dates_chronology(self):
        dates = {
            'offer_date': self.offer_date,
            'subscription_deadline': self.subscription_deadline,
            'payment_deadline': self.payment_deadline,
            'allotment_date': self.allotment_date
        }
        self.validate_dates_chronology(dates)

    @model_validator(mode='after')
    def validate_allotment_data(self):
        if any([self.shares_allotted, self.allotment_ratio]) and not self.allotment_date:
            raise ValueError("Allotment date must be provided if shares_allotted or allotment_ratio is provided")

    model_config = ConfigDict(
        extra="forbid")


class SubscriptionResponse(CorporateActionResponse):
    subscription_price: float
    subscription_ratio: float
    minimum_subscription: Optional[int] = None
    maximum_subscription: Optional[int] = None
    offer_date: date
    subscription_deadline: date
    payment_deadline: date
    allotment_date: Optional[date] = None
    shares_applied: Optional[int] = None
    shares_allotted: Optional[int] = None
    allotment_ratio: Optional[float] = None
    subscription_purpose: Optional[str] = None
    subscription_notes: Optional[str] = None
