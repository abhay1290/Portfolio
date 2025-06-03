from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError

from equity.src.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, \
    CorporateActionResponse
from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class DelistingRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.DELISTING, frozen=True,
                                                 description="Type of corporate action")
    # Delisting details
    delisting_reason: str = Field(..., max_length=255, description="Reason for the delisting")
    is_voluntary: bool = Field(False, description="Whether the delisting was voluntary")
    final_trading_date: date = Field(..., description="Last date the security will trade on this exchange")

    # New trading venue (if applicable)
    new_exchange: Optional[str] = Field(None, max_length=100,
                                        description="New exchange if security continues trading elsewhere")
    new_symbol: Optional[str] = Field(None, max_length=20, description="New trading symbol if applicable")
    new_security_type: Optional[str] = Field(None, max_length=50,
                                             description="Type of new security if applicable (Private, OTC, Other Exchange)")

    # Dates
    announcement_date: date = Field(..., description="Date when delisting was first announced")
    notification_date: Optional[date] = Field(None, description="Date when delisting was announced")
    effective_date: date = Field(..., description="Date when delisting becomes effective")
    appeal_deadline: Optional[date] = Field(None, description="Deadline for appealing the delisting decision")

    # Valuation impact
    last_trading_price: Optional[float] = Field(None, ge=0, description="Last trading price before delisting")
    implied_liquidation_value: Optional[float] = Field(None, ge=0, description="Implied liquidation value per share")

    # @field_validator('delisting_reason')
    # def validate_delisting_reason(cls, v):
    #     if v not in DELISTING_REASONS:
    #         raise PydanticCustomError(
    #             "invalid_reason",
    #             f"Delisting reason must be one of: {', '.join(DELISTING_REASONS)}"
    #         )
    #     return v
    #
    # @field_validator('new_security_type')
    # def validate_security_type(cls, v):
    #     if v is not None and v not in SECURITY_TYPES:
    #         raise PydanticCustomError(
    #             "invalid_security_type",
    #             f"Security type must be one of: {', '.join(SECURITY_TYPES)} or None"
    #         )
    #     return v

    @model_validator(mode='after')
    def validate_dates_chronology(self):
        if self.notification_date and self.final_trading_date < self.notification_date:
            raise PydanticCustomError(
                "invalid_date",
                "Final trading date must be after notification date"
            )

        if self.final_trading_date > self.effective_date:
            raise PydanticCustomError(
                "invalid_date",
                "Final trading date must be on or before effective date"
            )

        if self.appeal_deadline and self.effective_date < self.appeal_deadline:
            raise PydanticCustomError(
                "invalid_date",
                "Effective date must be after appeal deadline if specified"
            )

        if self.final_trading_date < self.announcement_date:
            raise PydanticCustomError(
                "invalid_date",
                "Final trading date cannot be before announcement date"
            )

        return self

    @model_validator(mode='after')
    def validate_new_trading_venue(self):
        if any([self.new_exchange, self.new_symbol, self.new_security_type]):
            if not all([self.new_exchange, self.new_symbol]):
                raise PydanticCustomError(
                    "missing_fields",
                    "Both new_exchange and new_symbol must be provided if new trading venue is specified"
                )
        return self

    model_config = ConfigDict(
        extra="forbid")


class DelistingResponse(CorporateActionResponse):
    # Delisting details
    delisting_reason: str
    is_voluntary: bool
    final_trading_date: date
    delisting_code: Optional[str] = None

    # New trading venue (if applicable)
    new_exchange: Optional[str] = None
    new_symbol: Optional[str] = None
    new_security_type: Optional[str] = None

    # Dates
    announcement_date: date
    notification_date: Optional[date] = None
    effective_date: date
    appeal_deadline: Optional[date] = None

    # Impact on shareholders
    shareholder_impact: Optional[str] = None
    alternative_trading_info: Optional[str] = None
    delisting_notes: Optional[str] = None

    # Valuation impact
    last_trading_price: Optional[float] = None
    implied_liquidation_value: Optional[float] = None
