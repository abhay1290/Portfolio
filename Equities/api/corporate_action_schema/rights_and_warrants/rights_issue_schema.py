# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from Equities.corporate_actions.enums.RightsStatusEnum import RightsStatusEnum


class RightsIssueRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.RIGHTS_ISSUE)

    # Rights Details
    subscription_price: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0)
    rights_ratio: condecimal(max_digits=10, decimal_places=6) = Field(..., gt=0)
    subscription_ratio: condecimal(max_digits=10, decimal_places=6) = Field(..., gt=0)

    # Key Dates
    announcement_date: Optional[date] = Field(None)
    ex_rights_date: date = Field(..., description="Ex-rights date")
    rights_trading_start: Optional[date] = Field(None)
    rights_trading_end: Optional[date] = Field(None)
    subscription_deadline: date = Field(..., description="Subscription deadline")

    # Rights Valuation
    theoretical_rights_value: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)
    rights_trading_price: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)

    # Status
    rights_status: RightsStatusEnum = Field(default=RightsStatusEnum.ACTIVE)

    # Additional Information
    rights_purpose: Optional[constr(max_length=1000)] = Field(None)
    rights_notes: Optional[constr(max_length=2000)] = Field(None)

    model_config = ConfigDict(extra="forbid")


class RightsIssueResponse(CorporateActionResponse):
    subscription_price: float
    rights_ratio: float
    subscription_ratio: float
    announcement_date: Optional[date] = None
    ex_rights_date: date
    rights_trading_start: Optional[date] = None
    rights_trading_end: Optional[date] = None
    subscription_deadline: date
    theoretical_rights_value: Optional[float] = None
    rights_trading_price: Optional[float] = None
    rights_status: RightsStatusEnum
    rights_purpose: Optional[str] = None
    rights_notes: Optional[str] = None
