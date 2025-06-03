# Corporate Action Pydantic Request/Response Models
from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic.types import condecimal

from equity.src.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, \
    CorporateActionResponse
from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum

AcquisitionMethod = Literal['CASH', 'STOCK', 'MIXED']


class AcquisitionRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.ACQUISITION, frozen=True,
                                                 description="Type of corporate action")

    # Acquisition Information
    acquiring_company_id: Optional[int] = Field(None, gt=0, description="ID of the acquiring company")
    acquisition_price: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0,
                                                                           description="Per-share acquisition price")
    acquisition_premium: Optional[float] = Field(None, ge=0.0, description="Premium percentage offered")
    shares_exchanged: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, gt=0,
                                                                                    description="Number of shares exchanged (for stock acquisitions)")
    exchange_ratio: Optional[float] = Field(None, gt=0, description="Exchange ratio (for stock acquisitions)")

    # Key Dates
    announcement_date: date = Field(..., description="Date when acquisition was announced")
    expected_completion_date: date = Field(..., description="Expected completion date")
    completion_date: Optional[date] = Field(None, description="Actual completion date (populated when completed)")

    # Transaction Details
    acquisition_method: AcquisitionMethod = Field(..., description="Acquisition method (CASH, STOCK, or MIXED)")
    is_friendly: bool = Field(default=True, description="Whether the acquisition is friendly")
    premium_over_market: Optional[float] = Field(None, ge=0.0, description="Premium over market price")

    # Additional Information
    acquisition_notes: Optional[str] = Field(None, max_length=2000,
                                             description="Additional notes about the acquisition")

    @model_validator(mode='after')
    def validate_stock_acquisition_fields(self) -> 'AcquisitionRequest':
        if self.acquisition_method == 'STOCK':
            if self.exchange_ratio is None:
                raise ValueError("exchange_ratio must be provided for stock acquisitions")
            if self.shares_exchanged is None:
                raise ValueError("shares_exchanged must be provided for stock acquisitions")
        elif self.acquisition_method == 'CASH':
            if self.exchange_ratio is not None or self.shares_exchanged is not None:
                raise ValueError("exchange_ratio and shares_exchanged should not be provided for cash acquisitions")
        return self

    @classmethod
    @field_validator('expected_completion_date')
    def validate_expected_completion_date(cls, v: date, info):
        if 'announcement_date' in info.data and v < info.data['announcement_date']:
            raise ValueError("Expected completion date must be after announcement date")
        return v

    model_config = ConfigDict(extra="forbid")


class AcquisitionResponse(CorporateActionResponse):
    # Acquisition Information
    acquiring_company_id: Optional[int] = None
    acquisition_price: Decimal
    acquisition_premium: Optional[float] = None
    shares_exchanged: Optional[Decimal] = None
    exchange_ratio: Optional[float] = None

    # Dates
    announcement_date: date
    expected_completion_date: date
    completion_date: Optional[date] = None

    # Transaction Details
    acquisition_method: AcquisitionMethod
    is_friendly: bool
    is_completed: bool = Field(
        default=False,
        description="Whether the acquisition has been completed"
    )
    premium_over_market: Optional[float] = None

    # Calculated Fields
    total_acquisition_value: Optional[Decimal] = Field(
        None,
        description="Total value of the acquisition"
    )
    implied_equity_value: Optional[Decimal] = Field(
        None,
        description="Implied equity value from acquisition"
    )

    # Additional Information
    acquisition_notes: Optional[str] = None
