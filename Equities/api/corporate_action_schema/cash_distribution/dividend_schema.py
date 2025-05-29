from datetime import datetime
from typing import Optional

from pydantic import ConfigDict, Field, PositiveFloat, condecimal, field_validator

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.DividendFrequencyEnum import DividendFrequencyEnum
from Equities.corporate_actions.enums.DividendTypeEnum import DividendTypeEnum
from Equities.corporate_actions.enums.TaxStatusEnum import TaxStatusEnum


class DividendRequest(CorporateActionRequest):
    # Financial Dividend Info
    dividend_type: DividendTypeEnum
    dividend_amount: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0)
    dividend_frequency: Optional[DividendFrequencyEnum] = Field(None, description="Dividend payout frequency")

    # Key Dates
    declaration_date: datetime = Field(..., description="Date dividend was declared")
    ex_dividend_date: Optional[datetime] = Field(None, description="Date on which dividend becomes ex-dividend")
    payment_date: datetime = Field(..., description="Date dividend will be paid")

    # Additional Metadata
    tax_status: Optional[TaxStatusEnum] = None
    gross_dividend: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)
    net_dividend: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)
    withholding_tax_rate: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Derived/Optional
    dividend_yield: Optional[PositiveFloat] = Field(None,
                                                    description="Dividend yield in decimal format (e.g., 0.05 for 5%)")
    notes: Optional[str] = Field(None, description="Any additional notes")

    @classmethod
    @field_validator('payment_date')
    def check_payment_after_declaration(cls, v, values):
        declaration_date = values.get('declaration_date')
        if declaration_date and v < declaration_date:
            raise ValueError("payment_date must be after declaration_date")
        return v

    @classmethod
    @field_validator('gross_dividend', 'net_dividend')
    def check_non_negative_amounts(cls, v):
        if v is not None and v < 0:
            raise ValueError("Dividend amounts must be non-negative")
        return v

    model_config = ConfigDict(extra="forbid")


class DividendResponse(CorporateActionResponse):
    # Financial Dividend Info
    dividend_type: DividendTypeEnum
    dividend_amount: float
    dividend_frequency: Optional[DividendFrequencyEnum]

    # Key Dates
    declaration_date: datetime
    ex_dividend_date: Optional[datetime]
    payment_date: datetime

    # Additional Metadata
    tax_status: Optional[TaxStatusEnum] = None
    gross_dividend: Optional[float] = None
    net_dividend: Optional[float] = None
    withholding_tax_rate: Optional[float] = None

    # Derived/Optional
    dividend_yield: Optional[float] = None
    notes: Optional[str] = None
