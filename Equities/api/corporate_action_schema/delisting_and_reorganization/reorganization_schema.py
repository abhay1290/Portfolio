from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict, Field, field_validator

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse


class ReorganizationRequest(CorporateActionRequest):
    # Reorganization details
    reorganization_type: str = Field(..., max_length=100,
                                     description="Type of reorganization (e.g., 'Merger', 'Spin-off', 'Split-off')")
    new_entity_id: Optional[int] = Field(None, description="ID of the new entity created by the reorganization")

    # Exchange terms
    exchange_ratio: Optional[Decimal] = Field(None, max_digits=10, decimal_places=6,
                                              description="Ratio at which shares are exchanged (if applicable)")
    cash_component: Optional[Decimal] = Field(None, max_digits=20, decimal_places=6,
                                              description="Cash amount per share in the reorganization")

    # Dates
    announcement_date: Optional[date] = Field(None, description="Date reorganization was announced")
    shareholder_approval_date: Optional[date] = Field(None, description="Date shareholders approved the reorganization")
    effective_date: date = Field(..., description="Date reorganization becomes effective")

    # Tax implications
    is_tax_free: bool = Field(False, description="Whether the reorganization qualifies as tax-free")

    # Metadata
    reorganization_purpose: Optional[str] = Field(None, description="Purpose or rationale for the reorganization")
    reorganization_notes: Optional[str] = Field(None, description="Additional notes about the reorganization")

    @classmethod
    @field_validator('shareholder_approval_date', 'effective_date')
    def check_dates_after_announcement(cls, v, values):
        announcement_date = values.get('announcement_date')
        if announcement_date and v and v < announcement_date:
            raise ValueError("Approval and effective dates must be after announcement date")
        return v

    @classmethod
    @field_validator('effective_date')
    def check_effective_after_approval(cls, v, values):
        approval_date = values.get('shareholder_approval_date')
        if approval_date and v and v < approval_date:
            raise ValueError("Effective date must be after shareholder approval date")
        return v

    @classmethod
    @field_validator('exchange_ratio', 'cash_component')
    def check_non_negative_values(cls, v):
        if v is not None and v < 0:
            raise ValueError("Exchange terms must be non-negative")
        return v

    model_config = ConfigDict(extra="forbid")


class ReorganizationResponse(CorporateActionResponse):
    # Reorganization details
    reorganization_type: str
    new_entity_id: Optional[int] = None

    # Exchange terms
    exchange_ratio: Optional[Decimal] = None
    cash_component: Optional[Decimal] = None

    # Dates
    announcement_date: Optional[date] = None
    shareholder_approval_date: Optional[date] = None
    effective_date: date

    # Tax implications
    is_tax_free: bool = False

    # Metadata
    reorganization_purpose: Optional[str] = None
    reorganization_notes: Optional[str] = None
