# Corporate Action Pydantic Request/Response Models
from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic.types import condecimal, constr

from equity.src.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, \
    CorporateActionResponse
from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class TenderOfferRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.TENDER_OFFER, frozen=True,
                                                 description="Type of corporate action")

    # Tender Offer Details
    offer_price: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0,
                                                                     description="Price per share being offered")
    minimum_shares_sought: Optional[int] = Field(None, gt=0, description="Minimum shares sought for offer to proceed")
    maximum_shares_sought: Optional[int] = Field(None, gt=0, description="Maximum shares the offer will accept")

    # Key Dates
    offer_date: date = Field(..., description="Date when tender offer begins")
    expiration_date: date = Field(..., description="Date when tender offer expires")
    withdrawal_deadline: Optional[date] = Field(None,
                                                description="Deadline for shareholders to withdraw tendered shares")
    proration_date: Optional[date] = Field(None,
                                           description="Date used to determine proration if offer is oversubscribed")
    completion_date: Optional[date] = Field(None, description="Actual completion date when known")

    # Offer Conditions
    offer_type: Literal['CASH', 'STOCK', 'MIXED'] = Field(default='CASH',
                                                          description="Type of consideration being offered")
    is_conditional: bool = Field(default=False, description="Whether the offer has conditions")
    minimum_tender_condition: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                      description="Minimum percentage of shares that must be tendered")
    is_going_private: bool = Field(default=False, description="Whether this is a going-private transaction")

    # Additional Information
    offer_terms: Optional[constr(max_length=5000)] = Field(None, description="Detailed terms of the tender offer")
    tender_notes: Optional[constr(max_length=2000)] = Field(None, description="Additional notes about the tender offer")

    # Validators
    @classmethod
    @field_validator('expiration_date')
    def validate_expiration_after_offer(cls, v, values):
        if 'offer_date' in values and v <= values['offer_date']:
            raise ValueError("Expiration date must be after offer date")
        return v

    @model_validator(mode='after')
    def validate_share_limits(self):
        if (self.minimum_shares_sought is not None and
                self.maximum_shares_sought is not None and
                self.minimum_shares_sought > self.maximum_shares_sought):
            raise ValueError("Minimum shares sought cannot exceed maximum shares sought")
        return self

    @model_validator(mode='after')
    def validate_withdrawal_deadline(self):
        if (self.withdrawal_deadline is not None and
                self.expiration_date is not None and
                self.withdrawal_deadline > self.expiration_date):
            raise ValueError("Withdrawal deadline cannot be after expiration date")
        return self

    model_config = ConfigDict(
        extra="forbid")


class TenderOfferResponse(CorporateActionResponse):
    offer_price: Decimal
    minimum_shares_sought: Optional[int] = None
    maximum_shares_sought: Optional[int] = None
    is_completed: bool = False
    offer_date: date
    expiration_date: date
    withdrawal_deadline: Optional[date] = None
    proration_date: Optional[date] = None
    completion_date: Optional[date] = None
    offer_type: str = "CASH"
    is_conditional: bool = False
    minimum_tender_condition: Optional[float] = None
    is_going_private: bool = False
    shares_tendered: Optional[int] = None
    shares_accepted: Optional[int] = None
    proration_factor: Optional[float] = None
    final_price: Optional[Decimal] = None
    premium_over_market: Optional[float] = None
    total_consideration: Optional[Decimal] = None
    offer_terms: Optional[str] = None
    tender_notes: Optional[str] = None
