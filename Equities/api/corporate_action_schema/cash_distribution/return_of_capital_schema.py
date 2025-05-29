# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class ReturnOfCapitalRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.RETURN_OF_CAPITAL)

    # Financial Information
    return_amount: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0)
    cost_basis_reduction: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)

    # Key Dates
    declaration_date: date = Field(..., description="Declaration date")
    ex_date: Optional[date] = Field(None, description="Ex-date")
    payment_date: date = Field(..., description="Payment date")

    # Impact Information
    affects_cost_basis: bool = Field(default=True, description="Whether this affects cost basis")

    # Additional Information
    return_reason: Optional[constr(max_length=1000)] = Field(None)
    return_notes: Optional[constr(max_length=2000)] = Field(None)

    model_config = ConfigDict(extra="forbid")


class ReturnOfCapitalResponse(CorporateActionResponse):
    return_amount: float
    cost_basis_reduction: Optional[float] = None
    declaration_date: date
    ex_date: Optional[date] = None
    payment_date: date
    affects_cost_basis: bool
    return_reason: Optional[str] = None
    return_notes: Optional[str] = None
