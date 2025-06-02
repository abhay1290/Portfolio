# Corporate Action Pydantic Request/Response Models
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import AfterValidator, ConfigDict, Field, model_validator
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class WarrantExerciseRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.WARRANT_EXERCISE, frozen=True,
                                                 description="Type of corporate action")

    # Warrant Details
    exercise_price: Decimal = Field(..., max_digits=20, decimal_places=6, gt=0,
                                    description="Price at which each warrant can be exercised into shares")

    warrant_ratio: Decimal = Field(..., max_digits=10, decimal_places=6, gt=0,
                                   description="Number of warrants issued per share")

    exercise_ratio: Decimal = Field(..., max_digits=10, decimal_places=6, gt=0,
                                    description="Number of shares received per warrant exercised")

    # Key Dates
    ex_warrant_date: date = Field(..., description="First date when warrants trade separately from shares")
    warrant_trading_start: Optional[date] = Field(None,
                                                  description="Date when warrant trading begins (if different from ex-warrant date)")
    warrant_trading_end: Optional[date] = Field(None,
                                                description="Last date when warrants can be traded before exercise deadline")
    exercise_deadline: date = Field(..., description="Last date to exercise warrants")
    settlement_date: Optional[date] = Field(None, description="Date when exercised shares are delivered to investors")

    # Exercise Conditions
    is_cashless_exercise: bool = Field(default=False,
                                       description="Whether the exercise can be done without cash payment (shares-for-warrants)")
    minimum_exercise_quantity: Optional[Annotated[
        int, Field(gt=0, description="Minimum number of warrants that can be exercised at once"), AfterValidator(
            lambda x: None if x == 0 else x)]] = None

    # Valuation
    theoretical_warrant_value: Optional[Annotated[condecimal(max_digits=20, decimal_places=6), Field(ge=0,
                                                                                                     description="Theoretical value of the warrant based on Black-Scholes or similar model")]] = None

    warrant_trading_price: Optional[Annotated[condecimal(max_digits=20, decimal_places=6), Field(ge=0,
                                                                                                 description="Current market price of the warrant")]] = None

    intrinsic_value: Optional[Annotated[condecimal(max_digits=20, decimal_places=6), Field(ge=0,
                                                                                           description="Immediate exercise value (max(0, stock_price - exercise_price))")]] = None

    time_value: Optional[Annotated[condecimal(max_digits=20, decimal_places=6), Field(ge=0,
                                                                                      description="Value attributable to remaining time until expiration")]] = None

    # Metadata
    warrant_terms: Optional[constr(max_length=5000, strip_whitespace=True)] = Field(None,
                                                                                    description="Detailed terms and conditions of the warrant exercise")
    exercise_notes: Optional[constr(max_length=2000, strip_whitespace=True)] = Field(None,
                                                                                     description="Additional notes about the warrant exercise process")

    # Cross-field validations
    @model_validator(mode='after')
    def validate_dates_chronology(self):
        if self.ex_warrant_date > self.exercise_deadline:
            raise ValueError("Ex-warrant date must be before exercise deadline")

        if self.warrant_trading_start and self.warrant_trading_end:
            if self.warrant_trading_start > self.warrant_trading_end:
                raise ValueError("Warrant trading start must be before end date")
            if self.warrant_trading_end > self.exercise_deadline:
                raise ValueError("Warrant trading must end before exercise deadline")

        if self.settlement_date and self.exercise_deadline > self.settlement_date:
            raise ValueError("Exercise deadline must be before settlement date")

    model_config = ConfigDict(
        extra="forbid")


class WarrantExerciseResponse(CorporateActionResponse):
    exercise_price: float
    warrant_ratio: float
    exercise_ratio: float
    ex_warrant_date: date
    warrant_trading_start: Optional[date] = None
    warrant_trading_end: Optional[date] = None
    exercise_deadline: date
    settlement_date: Optional[date] = None
    is_cashless_exercise: bool
    minimum_exercise_quantity: Optional[int] = None
    theoretical_warrant_value: Optional[float] = None
    warrant_trading_price: Optional[float] = None
    intrinsic_value: Optional[float] = None
    time_value: Optional[float] = None
    warrant_terms: Optional[str] = None
    exercise_notes: Optional[str] = None
