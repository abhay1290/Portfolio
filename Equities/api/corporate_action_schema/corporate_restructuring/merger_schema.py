# Corporate Action Pydantic Request/Response Models
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from Equities.corporate_actions.enums.MergerTypeEnum import MergerTypeEnum


class MergerRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.MERGER, frozen=True,
                                                 description="Type of corporate action")

    # Merger Information
    acquiring_company_id: Optional[int] = Field(None, gt=0, description="ID of the acquiring company if applicable")
    merger_type: MergerTypeEnum = Field(..., description="Type of merger (STATUTORY, CONSOLIDATION, etc.)")

    # Consideration Details
    cash_consideration: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0,
                                                                                      description="Cash amount per share to be paid")
    stock_consideration_ratio: Optional[condecimal(max_digits=10, decimal_places=6)] = Field(None, gt=0,
                                                                                             description="Ratio of acquiring company shares to be received")
    total_consideration_value: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0,
                                                                                             description="Total value of the merger consideration")
    fractional_shares_handling: str = Field(default="ROUND",
                                            description="How to handle fractional shares (ROUND, PAY_CASH, FLOOR)")

    # Key Dates
    announcement_date: date = Field(..., description="Date when merger was announced")
    shareholder_approval_date: Optional[date] = Field(None, description="Date when shareholders approved the merger")
    effective_date: date = Field(..., description="Legal effective date of the merger")
    completion_date: Optional[date] = Field(None, description="Actual completion date when known")

    # Tax Information
    is_tax_free_reorganization: bool = Field(default=False,
                                             description="Whether the merger qualifies as tax-free reorganization")
    taxable_gain_recognition: bool = Field(default=True, description="Whether taxable gains need to be recognized")

    # Financial Impact
    synergy_estimate: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0,
                                                                                    description="Estimated synergies from the merger")

    # Additional Information
    merger_terms: Optional[constr(max_length=5000)] = Field(None, description="Detailed terms of the merger")
    merger_notes: Optional[constr(max_length=2000)] = Field(None, description="Additional notes about the merger")

    # Validators
    @classmethod
    @field_validator('fractional_shares_handling')
    def validate_fractional_shares(cls, v):
        if v not in {'ROUND', 'PAY_CASH', 'FLOOR'}:
            raise ValueError("Fractional shares handling must be ROUND, PAY_CASH, or FLOOR")
        return v

    @classmethod
    @field_validator('announcement_date', 'effective_date')
    def validate_required_dates(cls, v):
        if v is None:
            raise ValueError("Date cannot be None")
        return v

    @model_validator(mode='after')
    def validate_date_sequence(self):
        if self.announcement_date and self.effective_date:
            if self.announcement_date >= self.effective_date:
                raise ValueError("Announcement date must be before effective date")
        if self.shareholder_approval_date and self.effective_date:
            if self.shareholder_approval_date > self.effective_date:
                raise ValueError("Shareholder approval date cannot be after effective date")
        return self

    @model_validator(mode='after')
    def validate_consideration(self):
        if self.cash_consideration is None and self.stock_consideration_ratio is None:
            raise ValueError("At least one consideration type (cash or stock) must be provided")
        return self

    model_config = ConfigDict(
        extra="forbid")


class MergerResponse(CorporateActionResponse):
    acquiring_company_id: Optional[int] = None
    merger_type: MergerTypeEnum
    is_completed: bool = False
    cash_consideration: Optional[Decimal] = None
    stock_consideration_ratio: Optional[Decimal] = None
    total_consideration_value: Optional[Decimal] = None
    fractional_shares_handling: str = "ROUND"
    announcement_date: date
    shareholder_approval_date: Optional[date] = None
    effective_date: date
    completion_date: Optional[date] = None
    is_tax_free_reorganization: bool = False
    taxable_gain_recognition: bool = True
    implied_premium: Optional[float] = None
    synergy_estimate: Optional[Decimal] = None
    merger_terms: Optional[str] = None
    merger_notes: Optional[str] = None
