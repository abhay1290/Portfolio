# Corporate Action Pydantic Request/Response Models
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import AfterValidator, ConfigDict, Field, model_validator
from pydantic.types import constr

from equity.src.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, \
    CorporateActionResponse
from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class SubscriptionRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.SUBSCRIPTION, frozen=True,
                                                 description="Type of corporate action")

    # Subscription Details
    subscription_price: Decimal = Field(..., max_digits=20, decimal_places=6, gt=0,
                                        description="Price per share for the subscription offer")
    subscription_ratio: Decimal = Field(..., max_digits=10, decimal_places=6, gt=0,
                                        description="Ratio of new shares offered per existing share")
    # Optional Fields with Defaults
    minimum_subscription: Annotated[int, Field(default=1, gt=0), AfterValidator(lambda x: 1 if x == 0 else x)] = Field(
        description="Minimum number of shares that can be subscribed")

    maximum_subscription: Annotated[
        int, Field(default=1000000, gt=0), AfterValidator(lambda x: 1000000 if x == 0 else x)] = Field(
        description="Maximum number of shares that can be subscribed")

    # Key Dates
    announcement_date: date = Field(default_factory=date.today, description="Announcement date")
    offer_date: date = Field(..., description="Subscription offer date")
    subscription_deadline: date = Field(..., description="Subscription deadline")
    payment_deadline: date = Field(..., description="Payment deadline")
    allotment_date: Optional[date] = Field(default=date.today(), description="Allotment date")

    # Results Fields (Optional)
    shares_applied: int = Field(default=0, ge=0, description="Number of shares applied for")
    shares_allotted: int = Field(default=0, ge=0, description="Number of shares allotted")
    allotment_ratio: float = Field(default=0.0, ge=0.0, le=1.0,
                                   description="Ratio of shares allotted to shares applied")
    subscription_premium: float = Field(default=0.0, ge=0, description="Premium percentage over market price")

    # Additional Information
    subscription_purpose: constr(max_length=1000) = Field(default="", description="Purpose of the subscription")
    subscription_notes: constr(max_length=2000) = Field(default="",
                                                        description="Additional notes about the subscription")

    @model_validator(mode='after')
    def validate_subscription_limits(self):
        if self.minimum_subscription > self.maximum_subscription:
            raise ValueError("Minimum subscription cannot be greater than maximum subscription")
        return self

    @model_validator(mode='after')
    def validate_dates(self):
        if self.offer_date > self.subscription_deadline:
            raise ValueError("Offer date must be before subscription deadline")
        if self.subscription_deadline > self.payment_deadline:
            raise ValueError("Subscription deadline must be before payment deadline")
        if self.payment_deadline > self.allotment_date:
            raise ValueError("Payment deadline must be before allotment date")
        return self

    # @model_validator(mode='after')
    # def validate_allotment_data(self):
    #     if any([self.shares_allotted, self.allotment_ratio]) and not self.allotment_date:
    #         raise HTTPException(
    #             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    #             detail="Allotment date must be provided if shares_allotted or allotment_ratio is provided"
    #         )

    model_config = ConfigDict(
        extra="forbid")


class SubscriptionResponse(CorporateActionResponse):
    subscription_price: float
    subscription_ratio: float
    minimum_subscription: int
    maximum_subscription: int

    announcement_date: date
    offer_date: date
    subscription_deadline: date
    payment_deadline: date
    allotment_date: date

    shares_applied: int
    shares_allotted: int
    allotment_ratio: float
    subscription_premium: float

    subscription_purpose: str
    subscription_notes: str
