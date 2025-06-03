from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from Currency.CurrencyEnum import CurrencyEnum
from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from equity.src.model.corporate_actions.enums.PriorityEnum import PriorityEnum
from equity.src.model.corporate_actions.enums.ProcessingModeEnum import ProcessingModeEnum
from equity.src.model.corporate_actions.enums.StatusEnum import StatusEnum


class CorporateActionRequest(BaseModel):
    # Primary identifiers
    equity_id: int = Field(..., gt=0, description="ID of the equity affected")

    # Core action details
    action_type: CorporateActionTypeEnum = Field(..., description="Type of corporate action")
    currency: CurrencyEnum = Field(..., description="Currency for the action")

    # Status and processing
    status: StatusEnum = Field(default=StatusEnum.PENDING, description="Current processing status")
    priority: PriorityEnum = Field(default=PriorityEnum.NORMAL, description="Processing priority")
    processing_mode: ProcessingModeEnum = Field(default=ProcessingModeEnum.AUTOMATIC,
                                                description="How this action should be processed")

    # Key dates
    record_date: date = Field(..., description="Record date for eligibility")
    execution_date: date = Field(..., description="Date when action takes effect")

    # Flags
    is_mandatory: bool = Field(default=True, description="Whether participation is mandatory")
    is_taxable: bool = Field(default=False, description="Whether the action has tax implications")

    # Timestamps (for responses only, should not be in requests)
    @classmethod
    @field_validator('execution_date')
    def validate_execution_date(cls, v: date, values):
        if 'record_date' in values and v < values['record_date']:
            raise ValueError("Execution date must be on or after record date")
        return v

    @classmethod
    @field_validator('equity_id')
    def validate_equity_id(cls, v: int):
        if v <= 0:
            raise ValueError("Equity ID must be positive")
        return v


class CorporateActionResponse(CorporateActionRequest):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
