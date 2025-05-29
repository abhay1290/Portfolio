# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class TenderOfferRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.TENDER_OFFER)

    # Tender Offer Details
    offer_price: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0)
    minimum_shares_sought: Optional[int] = Field(None, gt=0)
    maximum_shares_sought: Optional[int] = Field(None, gt=0)

    # Key Dates
    offer_date: date = Field(..., description="Tender offer date")
    expiration_date: date = Field(..., description="Offer expiration date")
    withdrawal_deadline: Optional[date] = Field(None)
    proration_date: Optional[date] = Field(None)

    # Offer Conditions
    is_conditional: bool = Field(default=False)
    minimum_tender_condition: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Results (populated after completion)
    shares_tendered: Optional[int] = Field(None, ge=0)
    proration_factor: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Additional Information
    offer_terms: Optional[constr(max_length=5000)] = Field(None)
    tender_notes: Optional[constr(max_length=2000)] = Field(None)

    @classmethod
    @field_validator('expiration_date')
    def validate_expiration_after_offer(cls, v, info):
        offer_date = info.data.get('offer_date')
        if offer_date and v <= offer_date:
            raise ValueError("expiration_date must be after offer_date")
        return v

    model_config = ConfigDict(extra="forbid")


class TenderOfferResponse(CorporateActionResponse):
    offer_price: float
    minimum_shares_sought: Optional[int] = None
    maximum_shares_sought: Optional[int] = None
    offer_date: date
    expiration_date: date
    withdrawal_deadline: Optional[date] = None
    proration_date: Optional[date] = None
    is_conditional: bool
    minimum_tender_condition: Optional[float] = None
    shares_tendered: Optional[int] = None
    proration_factor: Optional[float] = None
    offer_terms: Optional[str] = None
    tender_notes: Optional[str] = None
