from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class LiquidationRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.LIQUIDATION, frozen=True,
                                                 description="Type of corporate action")
    # Liquidation details
    liquidation_type: str = Field(..., max_length=100,
                                  description="Type of liquidation (e.g., 'Voluntary', 'Involuntary')")
    liquidation_value_per_share: Optional[Decimal] = Field(None, max_digits=20, decimal_places=6,
                                                           description="Value per share in liquidation", gt=0)
    priority_claims: Optional[Decimal] = Field(None, max_digits=20, decimal_places=6,
                                               description="Total claims with priority over shareholders", ge=0)

    # Dates
    announcement_date: Optional[date] = Field(None, description="Date liquidation was announced")
    petition_date: Optional[date] = Field(None,
                                          description="Date when bankruptcy petition was filed (for Chapter 7/11)")
    approval_date: Optional[date] = Field(None, description="Date when liquidation plan was approved")
    effective_date: date = Field(..., description="Date liquidation becomes effective")
    final_distribution_date: Optional[date] = Field(None, description="Date of final distribution to shareholders")

    # Distribution details
    cash_distribution: Optional[Decimal] = Field(None, max_digits=20, decimal_places=6,
                                                 description="Cash amount distributed per share", ge=0)
    asset_distribution_value: Optional[Decimal] = Field(None, max_digits=20, decimal_places=6,
                                                        description="Value of asset distribution per share", ge=0)
    distribution_currency: Optional[str] = Field(None, min_length=3, max_length=3,
                                                 description="ISO currency code for distributions")

    # Status
    is_complete: bool = Field(False, description="Whether the liquidation process is complete")
    # Recovery rates
    estimated_recovery_rate: Optional[Decimal] = Field(None, max_digits=10, decimal_places=6,
                                                       description="Estimated recovery rate (0-1 scale)", ge=0, le=1)
    actual_recovery_rate: Optional[Decimal] = Field(None, max_digits=10, decimal_places=6,
                                                    description="Actual recovery rate (0-1 scale)", ge=0, le=1)

    # Metadata
    liquidation_reason: Optional[str] = Field(None, description="Reason for the liquidation")
    liquidation_notes: Optional[str] = Field(None, description="Additional notes about the liquidation")

    # @field_validator('liquidation_type')
    # def validate_liquidation_type(cls, v):
    #     if v not in LIQUIDATION_TYPES:
    #         raise PydanticCustomError(
    #             "invalid_liquidation_type",
    #             f"Liquidation type must be one of: {', '.join(LIQUIDATION_TYPES)}"
    #         )
    #     return v
    @classmethod
    @field_validator('distribution_currency')
    def validate_currency_code(cls, v):
        if v is not None and not v.isalpha():
            raise PydanticCustomError(
                "invalid_currency",
                "Currency code must be 3 alphabetic characters"
            )
        return v.upper() if v else None

    @model_validator(mode='after')
    def validate_dates_chronology(self):
        if self.petition_date and self.petition_date > self.announcement_date:
            raise PydanticCustomError(
                "invalid_date",
                "Petition date cannot be after announcement date"
            )

        if self.approval_date and self.approval_date < self.announcement_date:
            raise PydanticCustomError(
                "invalid_date",
                "Approval date cannot be before announcement date"
            )

        if self.effective_date < self.announcement_date:
            raise PydanticCustomError(
                "invalid_date",
                "Effective date cannot be before announcement date"
            )

        if self.final_distribution_date and self.final_distribution_date < self.effective_date:
            raise PydanticCustomError(
                "invalid_date",
                "Final distribution date must be after effective date"
            )

        # For bankruptcy types, petition date should be present
        if self.liquidation_type in ["Chapter7", "Chapter11"] and not self.petition_date:
            raise PydanticCustomError(
                "missing_field",
                "Petition date is required for bankruptcy liquidations"
            )

        return self

    @model_validator(mode='after')
    def validate_distribution_values(self):
        if self.is_complete and not any([self.cash_distribution, self.asset_distribution_value]):
            raise PydanticCustomError(
                "missing_distribution",
                "Either cash or asset distribution must be specified for completed liquidations"
            )

        if self.actual_recovery_rate is not None and not (0 <= self.actual_recovery_rate <= 1):
            raise PydanticCustomError(
                "invalid_recovery_rate",
                "Actual recovery rate must be between 0 and 1"
            )

        return self

    model_config = ConfigDict(
        extra="forbid")


class LiquidationResponse(CorporateActionResponse):
    # Liquidation details
    liquidation_type: str
    liquidation_value_per_share: Decimal
    priority_claims: Optional[Decimal] = None

    # Dates
    announcement_date: date
    petition_date: Optional[date] = None
    approval_date: Optional[date] = None
    effective_date: date
    final_distribution_date: Optional[date] = None

    # Distribution details
    cash_distribution: Optional[Decimal] = None
    asset_distribution_value: Optional[Decimal] = None
    distribution_currency: Optional[str] = None

    # Status tracking
    is_complete: bool = False

    # Recovery rates
    estimated_recovery_rate: Optional[Decimal] = None
    actual_recovery_rate: Optional[Decimal] = None

    # Metadata
    liquidation_reason: Optional[str] = None
    liquidation_notes: Optional[str] = None
