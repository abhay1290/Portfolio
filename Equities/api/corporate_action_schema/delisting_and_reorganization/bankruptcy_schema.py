from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field, field_validator

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse


class BankruptcyRequest(CorporateActionRequest):
    # Bankruptcy details
    bankruptcy_type: str = Field(..., max_length=50, description="Type of bankruptcy (e.g., 'Chapter 7', 'Chapter 11')")
    filing_date: date = Field(..., description="Date bankruptcy was filed")

    # Recovery estimates
    estimated_recovery_rate: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                     description="Estimated recovery rate (0.0 to 1.0)")
    recovery_timeline: Optional[str] = Field(None, max_length=255, description="Estimated timeline for recovery")

    # Dates
    court_approval_date: Optional[date] = Field(None, description="Date bankruptcy plan was approved by court")
    plan_effective_date: Optional[date] = Field(None, description="Date bankruptcy plan became effective")

    # Impact
    trading_suspension_date: Optional[date] = Field(None, description="Date trading was suspended")
    is_trading_suspended: bool = Field(True, description="Whether trading is currently suspended")

    # Metadata
    court_jurisdiction: Optional[str] = Field(None, max_length=255,
                                              description="Jurisdiction where bankruptcy was filed")
    bankruptcy_notes: Optional[str] = Field(None, description="Any additional notes about the bankruptcy")

    @classmethod
    @field_validator('plan_effective_date', 'court_approval_date')
    def check_dates_after_filing(cls, v, values):
        filing_date = values.get('filing_date')
        if v and filing_date and v < filing_date:
            raise ValueError("Bankruptcy plan dates must be after filing date")
        return v

    @classmethod
    @field_validator('trading_suspension_date')
    def check_suspension_after_filing(cls, v, values):
        filing_date = values.get('filing_date')
        if v and filing_date and v < filing_date:
            raise ValueError("Trading suspension must be after filing date")
        return v

    model_config = ConfigDict(extra="forbid")


class BankruptcyResponse(CorporateActionResponse):
    # Bankruptcy details
    bankruptcy_type: str
    filing_date: date

    # Recovery estimates
    estimated_recovery_rate: Optional[float] = None
    recovery_timeline: Optional[str] = None

    # Dates
    court_approval_date: Optional[date] = None
    plan_effective_date: Optional[date] = None

    # Impact
    trading_suspension_date: Optional[date] = None
    is_trading_suspended: bool = True

    # Metadata
    court_jurisdiction: Optional[str] = None
    bankruptcy_notes: Optional[str] = None
