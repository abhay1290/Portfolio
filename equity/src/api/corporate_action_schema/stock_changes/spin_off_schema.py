# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic.types import condecimal, constr

from equity.src.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, \
    CorporateActionResponse
from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class SpinOffRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.SPIN_OFF, frozen=True,
                                                 description="Type of corporate action")

    # Spin-off Information
    spun_off_equity_id: int = Field(..., gt=0,
                                    description="Unique identifier of the equity being spun off (must be positive)")
    distribution_ratio: condecimal(max_digits=10, decimal_places=6) = Field(..., gt=0,
                                                                            description="Ratio of new shares distributed per old share held (must be positive)")

    # Key Dates
    announcement_date: Optional[date] = Field(None, description="Date when the spin-off was first announced (optional)")
    ex_date: date = Field(..., description="Ex-date when the security trades without the right to receive the spin-off")
    distribution_date: date = Field(..., description="Date when the spun-off shares are distributed to shareholders")

    # Cost Basis and Valuation
    parent_cost_basis_allocation: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                          description="Percentage (0-1) of cost basis allocated to parent company (optional)")
    spinoff_cost_basis_allocation: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                           description="Percentage (0-1) of cost basis allocated to spun-off company (optional)")
    spinoff_fair_value: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0,
                                                                                      description="Fair market value per share of the spun-off company (optional, must be non-negative)")
    cash_in_lieu_rate: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0,
                                                                                     description="Cash payment rate for fractional shares (optional, must be non-negative)")

    # Additional Information
    spinoff_reason: Optional[constr(max_length=1000)] = Field(None,
                                                              description="Brief description of the reason for the spin-off (optional, max 1000 chars)")
    spinoff_notes: Optional[constr(max_length=2000)] = Field(None,
                                                             description="Additional notes or details about the spin-off (optional, max 2000 chars)")

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
