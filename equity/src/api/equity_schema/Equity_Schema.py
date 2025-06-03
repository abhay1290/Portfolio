from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, confloat, conint, field_validator

from Currency.CurrencyEnum import CurrencyEnum
from equity.src.model.enums import BusinessDayConventionEnum
from equity.src.model.enums import CalendarEnum


class EquityBase(BaseModel):
    symbol: Annotated[str, Field(min_length=1, max_length=20, description="Unique ticker symbol for the equity")]
    currency: Annotated[CurrencyEnum, Field(description="Currency in which the equity is denominated")]

    market_price: Annotated[Optional[confloat(ge=0)], Field(None,
                                                            description="Latest market price of the equity with precision up to 6 decimal places")]
    shares_outstanding: Annotated[
        Optional[conint(ge=0)], Field(None, description="Total number of outstanding shares as a whole number")]
    float_shares: Annotated[
        Optional[conint(ge=0)], Field(None, description="Number of shares available to the public as a whole number")]
    market_cap: Annotated[Optional[confloat(ge=0)], Field(None,
                                                          description="Total market capitalization with precision up to 2 decimal places")]

    calendar: Annotated[
        CalendarEnum, Field(default=CalendarEnum.TARGET, description="Calendar used for business day calculations")]
    business_day_convention: Annotated[BusinessDayConventionEnum, Field(default=BusinessDayConventionEnum.FOLLOWING,
                                                                        description="Business day convention for date adjustments")]

    is_active: Annotated[bool, Field(default=True, description="Flag indicating if the equity is active")]
    is_locked: Annotated[
        bool, Field(default=False, description="Flag indicating if the equity is locked for processing")]

    # corporate_action_ids: Annotated[
    #     List[str], Field(default_factory=list, description="List of associated corporate action IDs")]

    @classmethod
    @field_validator('symbol')
    def validate_symbol(cls, v):
        if not v.isupper():
            raise ValueError("Symbol must be in uppercase")
        if not v.isalnum():
            raise ValueError("Symbol must contain only alphanumeric characters")
        return v

    model_config = ConfigDict(extra="forbid")


class EquityRequest(EquityBase):
    pass


class EquityResponse(EquityBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: Optional[int] = None
    last_processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
