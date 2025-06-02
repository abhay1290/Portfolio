from datetime import date
from typing import Literal, Optional

from pydantic import ConfigDict, Field, constr, field_validator, model_validator

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class BankruptcyRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.BANKRUPTCY,
                                                 description="Type of corporate action")

    # Bankruptcy details
    bankruptcy_type: Literal['Chapter 7', 'Chapter 11', 'Chapter 13', 'Other'] = Field(...,
                                                                                       description="Type of bankruptcy filing")
    filing_date: date = Field(..., description="Date when bankruptcy was filed")

    # Recovery estimates
    estimated_recovery_rate: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                     description="Estimated recovery rate (0.0 to 1.0)")
    recovery_timeline: Optional[constr(max_length=255)] = Field(None,
                                                                description="Estimated timeline for recovery process")

    # Dates
    court_approval_date: Optional[date] = Field(None, description="Date when bankruptcy plan was approved by court")
    plan_effective_date: Optional[date] = Field(None, description="Date when bankruptcy plan became effective")

    # Impact
    trading_suspension_date: Optional[date] = Field(None, description="Date when trading was suspended")
    is_trading_suspended: bool = Field(default=True, description="Whether trading is currently suspended")

    # Calculated fields
    estimated_recovery_value: Optional[float] = Field(None, ge=0.0, description="Estimated recovery value in currency")

    # Metadata
    court_jurisdiction: Optional[constr(max_length=255)] = Field(None,
                                                                 description="Court jurisdiction where bankruptcy was filed")
    bankruptcy_notes: Optional[str] = Field(None, description="Additional notes about the bankruptcy")

    # Validators
    @model_validator(mode='after')
    def validate_bankruptcy_dates(self):
        if (self.plan_effective_date and
                self.filing_date and
                self.plan_effective_date < self.filing_date):
            raise ValueError("Plan effective date must be after filing date")

        if (self.court_approval_date and
                self.filing_date and
                self.court_approval_date < self.filing_date):
            raise ValueError("Court approval date must be after filing date")

        if (self.trading_suspension_date and
                self.filing_date and
                self.trading_suspension_date < self.filing_date):
            raise ValueError("Trading suspension date must be after filing date")

        return self

    @classmethod
    @field_validator('estimated_recovery_rate')
    def validate_recovery_rate(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError("Recovery rate must be between 0 and 1")
        return v

    model_config = ConfigDict(
        extra="forbid")


class BankruptcyResponse(CorporateActionResponse):
    bankruptcy_type: str
    filing_date: date
    estimated_recovery_rate: Optional[float] = None
    recovery_timeline: Optional[str] = None
    court_approval_date: Optional[date] = None
    plan_effective_date: Optional[date] = None
    trading_suspension_date: Optional[date] = None
    is_trading_suspended: bool = True
    estimated_recovery_value: Optional[float] = None
    court_jurisdiction: Optional[str] = None
    bankruptcy_notes: Optional[str] = None
