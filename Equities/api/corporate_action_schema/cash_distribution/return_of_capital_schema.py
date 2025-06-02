# Corporate Action Pydantic Request/Response Models
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic.types import condecimal

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class ReturnOfCapitalRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(
        default=CorporateActionTypeEnum.RETURN_OF_CAPITAL,
        description="Type of corporate action"
    )

    # Financial Information
    return_amount: condecimal(max_digits=20, decimal_places=6) = Field(
        ...,
        gt=0,
        description="Per-share return of capital amount"
    )
    eligible_outstanding_shares: condecimal(max_digits=20, decimal_places=6) = Field(
        ...,
        gt=0,
        description="Number of shares eligible for return of capital"
    )
    cost_basis_reduction: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(
        None,
        ge=0,
        description="Per-share cost basis reduction amount"
    )

    # Key Dates
    declaration_date: date = Field(..., description="Declaration date")
    ex_date: Optional[date] = Field(None, description="Ex-date (first trading day without entitlement)")
    payment_date: date = Field(..., description="Payment date")

    # Impact Information
    affects_cost_basis: bool = Field(
        default=True,
        description="Whether this return of capital affects cost basis"
    )
    tax_rate: Optional[condecimal(max_digits=6, decimal_places=4)] = Field(
        None,
        ge=0,
        le=1,
        description="Applicable tax rate (0 to 1)"
    )

    # Additional Information
    return_notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Additional notes about the return of capital"
    )

    @model_validator(mode='after')
    def validate_cost_basis_fields(self) -> 'ReturnOfCapitalRequest':
        if self.affects_cost_basis and self.cost_basis_reduction is None:
            raise ValueError("cost_basis_reduction must be provided when affects_cost_basis is True")
        return self

    @classmethod
    @field_validator('payment_date')
    def validate_payment_date(cls, v: date, values):
        if 'declaration_date' in values and v < values['declaration_date']:
            raise ValueError("Payment date must be after declaration date")
        return v

    @classmethod
    @field_validator('ex_date')
    def validate_ex_date(cls, v: Optional[date], values):
        if v is not None:
            if 'declaration_date' in values and v < values['declaration_date']:
                raise ValueError("Ex-date must be after declaration date")
            if 'payment_date' in values and v > values['payment_date']:
                raise ValueError("Ex-date must be before payment date")
        return v

    model_config = ConfigDict(extra="forbid")


class ReturnOfCapitalResponse(CorporateActionResponse):
    # Financial Information
    return_amount: Decimal
    eligible_outstanding_shares: Decimal
    cost_basis_reduction: Optional[Decimal] = None
    total_return_amount: Optional[Decimal] = Field(
        None,
        description="Total return amount (return_amount * eligible_outstanding_shares)"
    )
    total_cost_basis_reduction: Optional[Decimal] = Field(
        None,
        description="Total cost basis reduction (cost_basis_reduction * eligible_outstanding_shares)"
    )

    # Dates
    declaration_date: date
    ex_date: Optional[date] = None
    payment_date: date

    # Impact Information
    affects_cost_basis: bool
    tax_rate: Optional[Decimal] = None

    # Additional Information
    return_notes: Optional[str] = None
