# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class SpinOffRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.SPIN_OFF)

    # Spin-off Information
    spun_off_equity_id: int = Field(..., gt=0, description="ID of the spun-off company")
    distribution_ratio: condecimal(max_digits=10, decimal_places=6) = Field(..., gt=0)

    # Key Dates
    announcement_date: Optional[date] = Field(None)
    ex_date: date = Field(..., description="Ex-date")
    distribution_date: date = Field(..., description="Distribution date")

    # Cost Basis and Valuation
    parent_cost_basis_allocation: Optional[float] = Field(None, ge=0.0, le=1.0)
    spinoff_cost_basis_allocation: Optional[float] = Field(None, ge=0.0, le=1.0)
    spinoff_fair_value: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)
    cash_in_lieu_rate: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)

    # Additional Information
    spinoff_reason: Optional[constr(max_length=1000)] = Field(None)
    spinoff_notes: Optional[constr(max_length=2000)] = Field(None)

    @classmethod
    @field_validator('spinoff_cost_basis_allocation')
    def validate_cost_basis_allocation(cls, v, info):
        parent_allocation = info.data.get('parent_cost_basis_allocation')
        if v is not None and parent_allocation is not None:
            if abs((v + parent_allocation) - 1.0) > 0.001:
                raise ValueError("parent_cost_basis_allocation + spinoff_cost_basis_allocation must equal 1.0")
        return v

    model_config = ConfigDict(extra="forbid")


class SpinOffResponse(CorporateActionResponse):
    spun_off_equity_id: int
    distribution_ratio: float
    announcement_date: Optional[date] = None
    ex_date: date
    distribution_date: date
    parent_cost_basis_allocation: Optional[float] = None
    spinoff_cost_basis_allocation: Optional[float] = None
    spinoff_fair_value: Optional[float] = None
    cash_in_lieu_rate: Optional[float] = None
    spinoff_reason: Optional[str] = None
    spinoff_notes: Optional[str] = None
