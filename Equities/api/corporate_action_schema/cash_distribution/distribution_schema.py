from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class DistributionRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.DISTRIBUTION)

    # Financial Information
    distribution_amount: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0)
    distribution_type: constr(max_length=100) = Field(..., description="Type of distribution")

    # Key Dates
    declaration_date: date = Field(..., description="Declaration date")
    ex_date: Optional[date] = Field(None, description="Ex-distribution date")
    payment_date: date = Field(..., description="Payment date")

    # Tax Information
    taxable_amount: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)
    non_taxable_amount: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)

    # Additional Information
    distribution_notes: Optional[constr(max_length=2000)] = Field(None)

    model_config = ConfigDict(extra="forbid")


class DistributionResponse(CorporateActionResponse):
    distribution_amount: float
    distribution_type: str
    declaration_date: date
    ex_date: Optional[date] = None
    payment_date: date
    taxable_amount: Optional[float] = None
    non_taxable_amount: Optional[float] = None
    distribution_notes: Optional[str] = None
