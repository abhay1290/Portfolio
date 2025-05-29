# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from Equities.corporate_actions.enums.TaxStatusEnum import TaxStatusEnum


class SpecialDividendRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.SPECIAL_DIVIDEND)

    # Financial Information
    special_dividend_amount: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0)
    gross_amount: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)
    net_amount: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)

    # Key Dates
    declaration_date: date = Field(..., description="Date special dividend was declared")
    ex_dividend_date: Optional[date] = Field(None, description="Ex-dividend date")
    payment_date: date = Field(..., description="Payment date")

    # Tax Information
    withholding_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    tax_status: Optional[TaxStatusEnum] = Field(None)

    # Additional Information
    dividend_reason: Optional[constr(max_length=1000)] = Field(None, description="Reason for special dividend")
    dividend_source: Optional[constr(max_length=255)] = Field(None, description="Source of dividend")
    special_dividend_notes: Optional[constr(max_length=2000)] = Field(None)

    @classmethod
    @field_validator('payment_date')
    def validate_payment_after_declaration(cls, v, info):
        declaration_date = info.data.get('declaration_date')
        if declaration_date and v < declaration_date:
            raise ValueError("payment_date must be after declaration_date")
        return v

    model_config = ConfigDict(extra="forbid")


class SpecialDividendResponse(CorporateActionResponse):
    special_dividend_amount: float
    gross_amount: Optional[float] = None
    net_amount: Optional[float] = None
    declaration_date: date
    ex_dividend_date: Optional[date] = None
    payment_date: date
    withholding_rate: Optional[float] = None
    tax_status: Optional[TaxStatusEnum] = None
    dividend_reason: Optional[str] = None
    dividend_source: Optional[str] = None
    special_dividend_notes: Optional[str] = None
