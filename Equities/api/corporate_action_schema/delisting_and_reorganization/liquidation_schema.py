from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict, Field, field_validator

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse


class LiquidationRequest(CorporateActionRequest):
    # Liquidation details
    liquidation_type: str = Field(..., max_length=100,
                                  description="Type of liquidation (e.g., 'Voluntary', 'Involuntary')")
    liquidation_value_per_share: Optional[Decimal] = Field(None, max_digits=20, decimal_places=6,
                                                           description="Value per share in liquidation")

    # Dates
    liquidation_announcement_date: Optional[date] = Field(None, description="Date liquidation was announced")
    liquidation_effective_date: date = Field(..., description="Date liquidation becomes effective")
    final_distribution_date: Optional[date] = Field(None, description="Date of final distribution to shareholders")

    # Distribution details
    cash_distribution: Optional[Decimal] = Field(None, max_digits=20, decimal_places=6,
                                                 description="Cash amount distributed per share")
    asset_distribution_value: Optional[Decimal] = Field(None, max_digits=20, decimal_places=6,
                                                        description="Value of asset distribution per share")

    # Status
    is_complete: bool = Field(False, description="Whether the liquidation process is complete")

    # Metadata
    liquidation_reason: Optional[str] = Field(None, description="Reason for the liquidation")
    liquidation_notes: Optional[str] = Field(None, description="Additional notes about the liquidation")

    @classmethod
    @field_validator('liquidation_effective_date', 'final_distribution_date')
    def check_dates_after_announcement(cls, v, values):
        announcement_date = values.get('liquidation_announcement_date')
        if announcement_date and v and v < announcement_date:
            raise ValueError("Effective and distribution dates must be after announcement date")
        return v

    @classmethod
    @field_validator('final_distribution_date')
    def check_distribution_after_effective(cls, v, values):
        effective_date = values.get('liquidation_effective_date')
        if effective_date and v and v < effective_date:
            raise ValueError("Final distribution date must be after effective date")
        return v

    @classmethod
    @field_validator(
        'liquidation_value_per_share',
        'cash_distribution',
        'asset_distribution_value'
    )
    def check_non_negative_values(cls, v):
        if v is not None and v < 0:
            raise ValueError("Financial values must be non-negative")
        return v

    model_config = ConfigDict(extra="forbid")


class LiquidationResponse(CorporateActionResponse):
    # Liquidation details
    liquidation_type: str
    liquidation_value_per_share: Optional[Decimal] = None

    # Dates
    liquidation_announcement_date: Optional[date] = None
    liquidation_effective_date: date
    final_distribution_date: Optional[date] = None

    # Distribution details
    cash_distribution: Optional[Decimal] = None
    asset_distribution_value: Optional[Decimal] = None

    # Status
    is_complete: bool = False

    # Metadata
    liquidation_reason: Optional[str] = None
    liquidation_notes: Optional[str] = None
