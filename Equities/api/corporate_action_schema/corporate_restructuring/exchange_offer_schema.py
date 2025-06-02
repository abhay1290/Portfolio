# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class ExchangeOfferRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.EXCHANGE_OFFER, frozen=True,
                                                 description="Type of corporate action")

    # Exchange Details
    new_security_id: int = Field(..., gt=0, description="ID of the new security")
    exchange_ratio: condecimal(max_digits=10, decimal_places=6) = Field(..., gt=0,
                                                                        description="Ratio at which securities will be exchanged")
    cash_component: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0,
                                                                                  description="Optional cash component per share")
    fractional_shares_handling: str = Field(default="ROUND",
                                            description="How to handle fractional shares (ROUND, PAY_CASH, FLOOR)")

    # Key Dates
    offer_date: date = Field(..., description="Exchange offer start date")
    expiration_date: date = Field(..., description="Offer expiration date")
    settlement_date: Optional[date] = Field(None, description="Actual settlement date when known")

    # Offer Conditions
    minimum_participation: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                   description="Minimum participation required for offer to proceed")
    is_voluntary: bool = Field(default=True, description="Whether the exchange is voluntary")

    # Additional Information
    exchange_terms: Optional[constr(max_length=5000)] = Field(None, description="Detailed terms of the exchange offer")
    exchange_notes: Optional[constr(max_length=2000)] = Field(None,
                                                              description="Additional notes about the exchange offer")

    @classmethod
    @field_validator('fractional_shares_handling')
    def validate_fractional_shares(cls, v):
        if v not in {'ROUND', 'PAY_CASH', 'FLOOR'}:
            raise ValueError("Fractional shares handling must be ROUND, PAY_CASH, or FLOOR")
        return v

    model_config = ConfigDict(
        extra="forbid")


class ExchangeOfferResponse(CorporateActionResponse):
    new_security_id: int
    exchange_ratio: condecimal(max_digits=10, decimal_places=6)
    cash_component: Optional[condecimal(max_digits=20, decimal_places=6)] = None
    fractional_shares_handling: str = "ROUND"
    offer_date: date
    expiration_date: date
    settlement_date: Optional[date] = None
    minimum_participation: Optional[float] = None
    is_voluntary: bool = True
    is_completed: bool = False
    exchange_terms: Optional[str] = None
    exchange_notes: Optional[str] = None
    implied_premium: Optional[float] = None
    participation_rate: Optional[float] = None
