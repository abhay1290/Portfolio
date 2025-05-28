from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, constr, field_validator

from Currency.CurrencyEnum import CurrencyEnum
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from Equities.corporate_actions.enums.StatusEnum import StatusEnum


class CorporateActionRequest(BaseModel):
    company_name: Optional[constr(max_length=256)] = Field(default=None,
                                                           description="Optional company name for the corporate action")
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.CASH_DIVIDEND,
                                                 description="Type of corporate action")
    currency: CurrencyEnum = Field(default=CurrencyEnum.USD, description="Currency of the corporate action")
    status: StatusEnum = Field(default=StatusEnum.PENDING, description="Processing status")
    record_date: date = Field(..., description="Record date for eligibility")
    effective_date: date = Field(..., description="Date action takes effect")
    details: Optional[constr(max_length=10000)] = Field(default=None, description="Additional details about the action")
    equity_id: int = Field(..., description="ID of the related equity (required)")

    model_config = ConfigDict(extra="forbid")

    @classmethod
    @field_validator("effective_date")
    def validate_date_order(cls, v, values):
        record_date = values.get("record_date")
        if record_date and v < record_date:
            raise ValueError("Effective date must be on or after record date")
        return v

    @classmethod
    @field_validator('equity_id')
    def check_equity_id_positive(cls, v):
        if v <= 0:
            raise ValueError("equity_id must be a positive integer")
        return v


class CorporateActionResponse(CorporateActionRequest):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
