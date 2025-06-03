# Corporate Action Pydantic Request/Response Models
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError

from equity.src.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, \
    CorporateActionResponse
from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from equity.src.model.corporate_actions.enums.RightsStatusEnum import RightsStatusEnum


class RightsIssueRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.RIGHTS_ISSUE, frozen=True,
                                                 description="Type of corporate action")

    # Rights Details
    subscription_price: Decimal = Field(..., max_digits=20, decimal_places=6, gt=0,
                                        description="Price at which rights can be exercised")
    rights_ratio: Decimal = Field(..., max_digits=10, decimal_places=6, gt=0,
                                  description="Ratio of rights offered per existing share")
    subscription_ratio: Decimal = Field(..., max_digits=10, decimal_places=6, gt=0,
                                        description="Ratio of new shares per right exercised")

    # Dates
    announcement_date: Optional[date] = Field(None, description="Date when rights issue was announced")
    ex_rights_date: date = Field(..., description="First date shares trade without rights")
    rights_trading_start: Optional[date] = Field(None, description="First date rights can be traded")
    rights_trading_end: Optional[date] = Field(None, description="Last date rights can be traded")
    subscription_deadline: date = Field(..., description="Deadline for exercising rights")

    # Rights valuation
    theoretical_rights_value: Optional[Decimal] = Field(None, max_digits=20, decimal_places=6, ge=0,
                                                        description="Theoretical value of the rights")
    rights_trading_price: Optional[Decimal] = Field(None, max_digits=20, decimal_places=6, ge=0,
                                                    description="Actual trading price of the rights")

    # Status tracking
    rights_status: RightsStatusEnum = Field(default=RightsStatusEnum.ACTIVE,
                                            description="Current status of the rights issue")

    # Metadata
    rights_purpose: Optional[str] = Field(None, max_length=1000,
                                          description="Purpose or rationale for the rights issue")
    rights_notes: Optional[str] = Field(None, max_length=2000, description="Additional notes about the rights issue")

    @model_validator(mode='after')
    def validate_dates_chronology(self):
        if self.announcement_date and self.ex_rights_date < self.announcement_date:
            raise PydanticCustomError(
                "invalid_date",
                "Ex-rights date cannot be before announcement date"
            )

        if self.rights_trading_start and self.rights_trading_end:
            if self.rights_trading_start > self.rights_trading_end:
                raise PydanticCustomError(
                    "invalid_date",
                    "Rights trading start date must be before end date"
                )

            if self.rights_trading_start > self.subscription_deadline:
                raise PydanticCustomError(
                    "invalid_date",
                    "Rights trading period must end before subscription deadline"
                )

        if self.ex_rights_date > self.subscription_deadline:
            raise PydanticCustomError(
                "invalid_date",
                "Ex-rights date must be before subscription deadline"
            )

        return self

    @model_validator(mode='after')
    def validate_rights_values(self):
        if self.theoretical_rights_value and self.rights_trading_price:
            if self.rights_trading_price > self.theoretical_rights_value * Decimal('1.5'):
                raise PydanticCustomError(
                    "invalid_valuation",
                    "Rights trading price appears too high relative to theoretical value"
                )

        if self.rights_status == RightsStatusEnum.EXPIRED and not self.subscription_deadline:
            raise PydanticCustomError(
                "invalid_status",
                "Cannot set status to EXPIRED without a subscription deadline"
            )

        return self

    model_config = ConfigDict(
        extra="forbid")


class RightsIssueResponse(CorporateActionResponse):
    # Rights details
    subscription_price: Decimal
    rights_ratio: Decimal
    subscription_ratio: Decimal

    # Dates
    announcement_date: Optional[date] = None
    ex_rights_date: date
    rights_trading_start: Optional[date] = None
    rights_trading_end: Optional[date] = None
    subscription_deadline: date

    # Rights valuation
    theoretical_rights_value: Optional[Decimal] = None
    rights_trading_price: Optional[Decimal] = None

    # Status tracking
    rights_status: RightsStatusEnum

    # Metadata
    rights_purpose: Optional[str] = None
    rights_notes: Optional[str] = None
