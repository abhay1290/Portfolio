from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict, Field, PositiveFloat, condecimal, field_validator

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.DividendFrequencyEnum import DividendFrequencyEnum
from Equities.corporate_actions.enums.TaxStatusEnum import TaxStatusEnum


class DividendRequest(CorporateActionRequest):
    # Financial Dividend Info
    dividend_amount: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0,
                                                                         description="Per-share dividend amount in the security's currency")
    dividend_frequency: Optional[DividendFrequencyEnum] = Field(None,
                                                                description="Frequency of dividend payments (e.g., QUARTERLY, ANNUAL)")
    gross_dividend: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0,
                                                                                  description="Gross dividend amount before any taxes or deductions")
    net_dividend: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0,
                                                                                description="Net dividend amount after all taxes and deductions")

    # Dividend Dates
    declaration_date: date = Field(..., description="Date when dividend was formally declared by the board")
    ex_dividend_date: Optional[date] = Field(None,
                                             description="First date when shares trade without dividend rights")
    payment_date: date = Field(..., description="Date when dividend will be paid to shareholders")

    # Tax Information
    dividend_tax_status: Optional[TaxStatusEnum] = Field(None,
                                                         description="Tax classification of the dividend (e.g., QUALIFIED, ORDINARY)")
    dividend_withholding_rate: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                       description="Withholding tax rate (0.0 to 1.0) for foreign investors")

    # Derived Metrics
    dividend_yield: Optional[PositiveFloat] = Field(None,
                                                    description="Current yield calculated as annual dividend / current price")

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

    @classmethod
    @field_validator('gross_dividend', 'net_dividend')
    def validate_dividend_amounts(cls, v: Optional[Decimal], values):
        if v is not None:
            if 'dividend_amount' in values and v > values['dividend_amount']:
                raise ValueError("Gross/Net dividend cannot exceed declared dividend amount")
        return v

    model_config = ConfigDict(extra="forbid")


class DividendResponse(CorporateActionResponse):
    # Inherits all fields from CorporateActionResponse
    corporate_action_id: int = Field(..., description="Foreign key to corporate action")

    # Mirror all fields from DividendRequest
    dividend_amount: Decimal
    dividend_frequency: Optional[DividendFrequencyEnum] = None
    gross_dividend: Optional[Decimal] = None
    net_dividend: Optional[Decimal] = None

    declaration_date: date
    ex_dividend_date: Optional[date] = None
    payment_date: date

    dividend_tax_status: Optional[TaxStatusEnum] = None
    dividend_withholding_rate: Optional[float] = None

    dividend_yield: Optional[float] = None
    dividend_notes: Optional[str] = None
