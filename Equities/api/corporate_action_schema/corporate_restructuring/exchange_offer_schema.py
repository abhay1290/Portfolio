# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class ExchangeOfferRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.EXCHANGE_OFFER)

    # Exchange Details
    new_security_id: int = Field(..., gt=0, description="ID of the new security")
    exchange_ratio: condecimal(max_digits=10, decimal_places=6) = Field(..., gt=0)
    cash_component: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)

    # Key Dates
    offer_date: date = Field(..., description="Exchange offer date")
    expiration_date: date = Field(..., description="Offer expiration date")
    settlement_date: Optional[date] = Field(None)

    # Offer Conditions
    minimum_participation: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_mandatory: bool = Field(default=False)

    # Additional Information
    exchange_terms: Optional[constr(max_length=5000)] = Field(None)
    exchange_notes: Optional[constr(max_length=2000)] = Field(None)

    model_config = ConfigDict(extra="forbid")


class ExchangeOfferResponse(CorporateActionResponse):
    new_security_id: int
    exchange_ratio: float
    cash_component: Optional[float] = None
    offer_date: date
    expiration_date: date
    settlement_date: Optional[date] = None
    minimum_participation: Optional[float] = None
    is_mandatory: bool
    exchange_terms: Optional[str] = None
    exchange_notes: Optional[str] = None
