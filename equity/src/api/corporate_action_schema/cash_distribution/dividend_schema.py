from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from pydantic import ConfigDict, Field, condecimal, field_validator
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from equity.src.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, \
    CorporateActionResponse
from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class DividendRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.DIVIDEND, frozen=True,
                                                 description="Type of corporate action")
    # Financial Dividend Info
    is_gross_dividend_amount: bool = Field(default=True,
                                           description="True if dividend_amount is gross amount (pre-tax), False if net amount")
    dividend_amount: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0,
                                                                         description="Per-share dividend amount in the security's currency")
    eligible_outstanding_shares: float = Field(..., gt=0,
                                               description="Number of outstanding shares eligible for dividend payment")

    # Dividend Dates
    declaration_date: date = Field(..., description="Date when dividend was formally declared by the board")
    ex_dividend_date: Optional[date] = Field(None, description="First date when shares trade without dividend rights")
    payment_date: date = Field(..., description="Date when dividend will be paid to shareholders")

    # Tax Information
    dividend_tax_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Tax rate (0.0 to 1.0) for investors")

    # Metadata
    dividend_notes: Optional[str] = Field(None, max_length=2000,
                                          description="Additional notes about the dividend declaration")

    @classmethod
    @field_validator('payment_date')
    def validate_payment_date(cls, v: date, values):
        if 'declaration_date' in values.data and v < values.data['declaration_date']:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "loc": ["body", "payment_date"],
                    "msg": "Payment date must be after declaration date",
                    "type": "date_order.invalid"
                }
            )
        return v

    @classmethod
    @field_validator('ex_dividend_date')
    def validate_ex_dividend_date(cls, v: Optional[date], values):
        if v is not None:
            data = values.data
            if 'declaration_date' in data and v < data['declaration_date']:
                raise HTTPException(
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "loc": ["body", "ex_dividend_date"],
                        "msg": "Ex-dividend date must be after declaration date",
                        "type": "date_order.invalid"
                    }
                )
            if 'payment_date' in data and v > data['payment_date']:
                raise HTTPException(
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "loc": ["body", "ex_dividend_date"],
                        "msg": "Ex-dividend date must be before payment date",
                        "type": "date_order.invalid"
                    }
                )
        return v

    model_config = ConfigDict(extra="forbid")


class DividendResponse(CorporateActionResponse):
    # Financial Information
    is_gross_dividend_amount: bool
    dividend_amount: Decimal
    eligible_outstanding_shares: float
    net_dividend_amount: Optional[Decimal]
    dividend_marketcap_in_dividend_currency: Optional[Decimal]

    # Dividend Dates
    declaration_date: date
    ex_dividend_date: Optional[date] = None
    payment_date: date

    # Tax Information
    dividend_tax_rate: Optional[float] = None

    # Metadata
    dividend_notes: Optional[str] = None
