# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class SubscriptionRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.SUBSCRIPTION)

    # Subscription Details
    subscription_price: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0)
    subscription_ratio: condecimal(max_digits=10, decimal_places=6) = Field(..., gt=0)
    minimum_subscription: Optional[int] = Field(None, gt=0)
    maximum_subscription: Optional[int] = Field(None, gt=0)

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

    model_config = ConfigDict(extra="forbid")


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
