from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict, Field, condecimal, field_validator

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse


class DividendRequest(CorporateActionRequest):
    # Financial Dividend Info
    is_gross_dividend_amount: bool = Field(default=True,
                                           description="True if dividend_amount is gross amount, False if net amount")
    dividend_amount: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0,
                                                                         description="Per-share dividend amount in the security's currency")
    eligible_outstanding_shares: float = Field(..., ge=0,
                                               description="Number of outstanding shares eligible for dividend payment at declaration date")

    # Dividend Dates
    declaration_date: date = Field(..., description="Date when dividend was formally declared by the board")
    ex_dividend_date: Optional[date] = Field(None, description="First date when shares trade without dividend rights")
    payment_date: date = Field(..., description="Date when dividend will be paid to shareholders")

    # Tax Information
    dividend_tax_rate: Optional[float] = Field(None, ge=0.0, le=1.0,
                                               description="Tax rate (0.0 to 1.0) for investors")

    # Metadata
    dividend_notes: Optional[str] = Field(None, max_length=500,
                                          description="Additional notes about the dividend declaration")

    # Field Validations
    @classmethod
    @field_validator('payment_date')
    def validate_payment_date(cls, v: date, values):
        if 'declaration_date' in values and v < values['declaration_date']:
            raise ValueError("Payment date must be after declaration date")
        return v

    @classmethod
    @field_validator('ex_dividend_date')
    def validate_ex_dividend_date(cls, v: Optional[date], values):
        if v is not None:
            if 'declaration_date' in values and v < values['declaration_date']:
                raise ValueError("Ex-dividend date must be after declaration date")
            if 'payment_date' in values and v > values['payment_date']:
                raise ValueError("Ex-dividend date must be before payment date")
        return v

    model_config = ConfigDict(extra="forbid")


class DividendResponse(CorporateActionResponse):
    # Inherits all fields from CorporateActionResponse
    corporate_action_id: int = Field(..., description="Foreign key to corporate action")

    # Mirror all fields from DividendRequest
    is_gross_dividend_amount: bool
    dividend_amount: Decimal
    eligible_outstanding_shares: float

    declaration_date: date
    ex_dividend_date: Optional[date] = None
    payment_date: date

    dividend_tax_rate: Optional[float] = None

    dividend_notes: Optional[str] = None
