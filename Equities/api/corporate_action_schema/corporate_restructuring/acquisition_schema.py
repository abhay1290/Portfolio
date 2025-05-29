# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class AcquisitionRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.ACQUISITION)

    # Acquisition Information
    acquiring_company_id: Optional[int] = Field(None, gt=0)
    acquisition_price: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0)
    acquisition_premium: Optional[float] = Field(None, ge=0.0)

    # Key Dates
    announcement_date: Optional[date] = Field(None)
    completion_date: date = Field(..., description="Acquisition completion date")

    # Transaction Details
    acquisition_method: Optional[constr(max_length=100)] = Field(None)
    is_friendly: bool = Field(default=True)
    premium_over_market: Optional[float] = Field(None, ge=0.0)

    # Additional Information
    acquisition_notes: Optional[constr(max_length=2000)] = Field(None)

    model_config = ConfigDict(extra="forbid")


class AcquisitionResponse(CorporateActionResponse):
    acquiring_company_id: Optional[int] = None
    acquisition_price: float
    acquisition_premium: Optional[float] = None
    announcement_date: Optional[date] = None
    completion_date: date
    acquisition_method: Optional[str] = None
    is_friendly: bool
    premium_over_market: Optional[float] = None
    acquisition_notes: Optional[str] = None
