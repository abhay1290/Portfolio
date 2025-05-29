from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field, field_validator

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse


class DelistingRequest(CorporateActionRequest):
    # Delisting details
    delisting_reason: str = Field(..., max_length=255, description="Reason for the delisting")
    is_voluntary: bool = Field(False, description="Whether the delisting was voluntary")
    final_trading_date: date = Field(..., description="Last date the security will trade on this exchange")

    # New trading venue (if applicable)
    new_exchange: Optional[str] = Field(None, max_length=100,
                                        description="New exchange if security continues trading elsewhere")
    new_symbol: Optional[str] = Field(None, max_length=20, description="New trading symbol if applicable")

    # Dates
    notification_date: Optional[date] = Field(None, description="Date when delisting was announced")
    effective_date: date = Field(..., description="Date when delisting becomes effective")

    # Impact on shareholders
    shareholder_impact: Optional[str] = Field(None, description="Description of impact on shareholders")
    delisting_notes: Optional[str] = Field(None, description="Any additional notes about the delisting")

    @classmethod
    @field_validator('effective_date', 'final_trading_date')
    def check_dates_chronology(cls, v, values):
        notification_date = values.get('notification_date')
        if notification_date and v and v < notification_date:
            raise ValueError("Effective and final trading dates must be after notification date")
        return v

    @classmethod
    @field_validator('final_trading_date')
    def check_final_before_effective(cls, v, values):
        effective_date = values.get('effective_date')
        if effective_date and v and v > effective_date:
            raise ValueError("Final trading date must be on or before effective date")
        return v

    model_config = ConfigDict(extra="forbid")


class DelistingResponse(CorporateActionResponse):
    # Delisting details
    delisting_reason: str
    is_voluntary: bool
    final_trading_date: date

    # New trading venue (if applicable)
    new_exchange: Optional[str] = None
    new_symbol: Optional[str] = None

    # Dates
    notification_date: Optional[date] = None
    effective_date: date

    # Impact on shareholders
    shareholder_impact: Optional[str] = None
    delisting_notes: Optional[str] = None
