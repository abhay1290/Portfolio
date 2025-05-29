# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from Equities.corporate_actions.enums.MergerTypeEnum import MergerTypeEnum


class MergerRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.MERGER)

    # Merger Information
    acquiring_company_id: Optional[int] = Field(None, gt=0)
    merger_type: MergerTypeEnum = Field(..., description="Type of merger")

    # Consideration Details
    cash_consideration: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)
    stock_consideration_ratio: Optional[condecimal(max_digits=10, decimal_places=6)] = Field(None, gt=0)
    total_consideration_value: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)

    # Key Dates
    announcement_date: Optional[date] = Field(None)
    shareholder_approval_date: Optional[date] = Field(None)
    effective_date: date = Field(..., description="Merger effective date")

    # Tax Information
    is_tax_free_reorganization: bool = Field(default=False)
    taxable_gain_recognition: bool = Field(default=True)

    # Additional Information
    merger_terms: Optional[constr(max_length=5000)] = Field(None)
    merger_notes: Optional[constr(max_length=2000)] = Field(None)

    model_config = ConfigDict(extra="forbid")


class MergerResponse(CorporateActionResponse):
    acquiring_company_id: Optional[int] = None
    merger_type: MergerTypeEnum
    cash_consideration: Optional[float] = None
    stock_consideration_ratio: Optional[float] = None
    total_consideration_value: Optional[float] = None
    announcement_date: Optional[date] = None
    shareholder_approval_date: Optional[date] = None
    effective_date: date
    is_tax_free_reorganization: bool
    taxable_gain_recognition: bool
    merger_terms: Optional[str] = None
    merger_notes: Optional[str] = None
