# Corporate Action Pydantic Request/Response Models
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic.types import condecimal

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class SpecialDividendRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.SPECIAL_DIVIDEND, frozen=True,
                                                 description="Type of corporate action")

    # Financial Information
    is_gross_dividend_amount: bool = Field(default=True,
                                           description="True if amount is gross (pre-tax), False if net amount")
    special_dividend_amount: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0,
                                                                                 description="Per-share special dividend amount")
    eligible_outstanding_shares: float = Field(..., gt=0, description="Number of shares eligible for special dividend")

    # Key Dates
    declaration_date: date = Field(..., description="Declaration date")
    ex_dividend_date: Optional[date] = Field(None,
                                             description="Ex-dividend date (first trading day without entitlement)")
    payment_date: date = Field(..., description="Payment date")

    # Tax Information
    dividend_tax_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Applicable tax rate (0.0 to 1.0)")

    # Additional Information
    special_dividend_notes: Optional[str] = Field(None, max_length=2000, description="Notes about the special dividend")

    @classmethod
    @field_validator('payment_date')
    def validate_payment_date(cls, v: date, info):
        if 'declaration_date' in info.data and v < info.data['declaration_date']:
            raise ValueError("Payment date must be after declaration date")
        return v

    @classmethod
    @field_validator('ex_dividend_date')
    def validate_ex_dividend_date(cls, v: Optional[date], info):
        if v is not None:
            if 'declaration_date' in info.data and v < info.data['declaration_date']:
                raise ValueError("Ex-dividend date must be after declaration date")
            if 'payment_date' in info.data and v > info.data['payment_date']:
                raise ValueError("Ex-dividend date must be before payment date")
        return v

    @model_validator(mode='after')
    def validate_tax_related_fields(self):
        if self.dividend_tax_rate is not None and self.dividend_tax_rate > 0:
            if not self.is_gross_dividend_amount:
                raise ValueError("Tax rate should only be provided for gross dividend amounts")
        return self

    model_config = ConfigDict(extra="forbid")


class SpecialDividendResponse(CorporateActionResponse):
    # Financial Information
    is_gross_dividend_amount: bool
    special_dividend_amount: Decimal
    eligible_outstanding_shares: float
    net_special_dividend_amount: Optional[Decimal] = Field(
        None,
        description="Net amount after tax deductions"
    )
    special_dividend_marketcap_in_dividend_currency: Optional[Decimal] = Field(
        None,
        description="Total payout amount (net amount * shares)"
    )

    # Dates
    declaration_date: date
    ex_dividend_date: Optional[date] = None
    payment_date: date

    # Tax Information
    dividend_tax_rate: Optional[float] = None

    # Additional Information
    special_dividend_notes: Optional[str] = None
