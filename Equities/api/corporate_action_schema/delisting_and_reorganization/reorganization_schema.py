from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class ReorganizationRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.REORGANIZATION, frozen=True,
                                                 description="Type of corporate action")
    # Reorganization details
    reorganization_type: str = Field(..., max_length=100,
                                     description="Type of reorganization (e.g., 'Merger', 'Spin-off', 'Split-off')")
    new_entity_id: Optional[int] = Field(None, description="ID of the new entity created by the reorganization")

    # Exchange terms
    exchange_ratio: Optional[Decimal] = Field(None, max_digits=10, decimal_places=6,
                                              description="Ratio at which shares are exchanged (if applicable)")
    cash_component: Optional[Decimal] = Field(None, max_digits=20, decimal_places=6,
                                              description="Cash amount per share in the reorganization")
    fractional_shares_handling: Optional[str] = Field(None, max_length=50,
                                                      description="How fractional shares are handled (Cash, Round-up, Round-down)")

    # Dates
    announcement_date: Optional[date] = Field(None, description="Date reorganization was announced")
    record_date: Optional[date] = Field(None, description="Date for determining shareholder eligibility")
    shareholder_meeting_date: Optional[date] = Field(None,
                                                     description="Date of shareholder meeting to approve the reorganization")
    shareholder_approval_date: Optional[date] = Field(None, description="Date shareholders approved the reorganization")
    effective_date: date = Field(..., description="Date reorganization becomes effective")

    # Tax implications
    is_tax_free: bool = Field(False, description="Whether the reorganization qualifies as tax-free")
    regulatory_approval_required: bool = Field(True, description="Whether regulatory approval is required")

    # Valuation
    implied_premium: Optional[Decimal] = Field(None, max_digits=10, decimal_places=6,
                                               description="Implied premium/discount to market price", ge=-1)
    pro_forma_impact: Optional[Decimal] = Field(None, max_digits=10, decimal_places=6,
                                                description="Pro forma EPS impact or other metric")

    # Metadata
    reorganization_purpose: Optional[str] = Field(None, description="Purpose or rationale for the reorganization")
    reorganization_notes: Optional[str] = Field(None, description="Additional notes about the reorganization")

    # @field_validator('reorganization_type')
    # def validate_reorganization_type(cls, v):
    #     if v not in REORGANIZATION_TYPES:
    #         raise PydanticCustomError(
    #             "invalid_reorganization_type",
    #             f"Reorganization type must be one of: {', '.join(REORGANIZATION_TYPES)}"
    #         )
    #     return v
    #
    # @field_validator('fractional_shares_handling')
    # def validate_fractional_handling(cls, v):
    #     if v is not None and v not in FRACTIONAL_SHARES_HANDLING:
    #         raise PydanticCustomError(
    #             "invalid_fractional_handling",
    #             f"Fractional shares handling must be one of: {', '.join(FRACTIONAL_SHARES_HANDLING)}"
    #         )
    #     return v

    @model_validator(mode='after')
    def validate_dates_chronology(self):
        if self.record_date and self.record_date < self.announcement_date:
            raise PydanticCustomError(
                "invalid_date",
                "Record date cannot be before announcement date"
            )

        if self.shareholder_meeting_date and self.shareholder_meeting_date < self.announcement_date:
            raise PydanticCustomError(
                "invalid_date",
                "Shareholder meeting date cannot be before announcement date"
            )

        if self.shareholder_approval_date and self.shareholder_approval_date < self.announcement_date:
            raise PydanticCustomError(
                "invalid_date",
                "Shareholder approval date cannot be before announcement date"
            )

        if self.effective_date < self.announcement_date:
            raise PydanticCustomError(
                "invalid_date",
                "Effective date cannot be before announcement date"
            )

        if self.completion_date and self.completion_date < self.effective_date:
            raise PydanticCustomError(
                "invalid_date",
                "Completion date must be after effective date"
            )

        # For certain types, new entity ID should be present
        if self.reorganization_type in ["Merger", "Spin-off", "Split-off"] and not self.new_entity_id:
            raise PydanticCustomError(
                "missing_field",
                "New entity ID is required for this reorganization type"
            )

        return self

    @model_validator(mode='after')
    def validate_exchange_terms(self):
        if not any([self.exchange_ratio, self.cash_component]):
            raise PydanticCustomError(
                "missing_terms",
                "Either exchange ratio or cash component must be specified"
            )

        if self.reorganization_type == "Spin-off" and self.cash_component is not None:
            raise PydanticCustomError(
                "invalid_terms",
                "Spin-offs typically don't have a cash component"
            )

        return self

    model_config = ConfigDict(
        extra="forbid")


class ReorganizationResponse(CorporateActionResponse):
    # Reorganization details
    reorganization_type: str
    new_entity_id: Optional[int] = None

    # Exchange terms
    exchange_ratio: Optional[Decimal] = None
    cash_component: Optional[Decimal] = None
    fractional_shares_handling: Optional[str] = None

    # Dates
    announcement_date: date
    record_date: Optional[date] = None
    shareholder_meeting_date: Optional[date] = None
    shareholder_approval_date: Optional[date] = None
    effective_date: date
    completion_date: Optional[date] = None

    # Tax and regulatory
    is_tax_free: bool = False
    regulatory_approval_required: bool = True

    # Valuation
    implied_premium: Optional[Decimal] = None
    pro_forma_impact: Optional[Decimal] = None

    # Metadata
    reorganization_purpose: Optional[str] = None
    reorganization_notes: Optional[str] = None
