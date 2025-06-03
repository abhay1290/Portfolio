# Corporate Action Pydantic Request/Response Models
from datetime import date

from pydantic import ConfigDict, Field, model_validator
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class WarrantExerciseRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.WARRANT_EXERCISE, frozen=True,
                                                 description="Type of corporate action")

    # Required Fields
    exercise_price: condecimal(max_digits=20, decimal_places=6, gt=0) = Field(
        ...,
        description="Price at which each warrant can be exercised into shares"
    )
    warrant_ratio: condecimal(max_digits=10, decimal_places=6, gt=0) = Field(
        ...,
        description="Number of warrants issued per share"
    )
    exercise_ratio: condecimal(max_digits=10, decimal_places=6, gt=0) = Field(
        ...,
        description="Number of shares received per warrant exercised"
    )
    ex_warrant_date: date = Field(
        ...,
        description="First date when warrants trade separately from shares"
    )
    exercise_deadline: date = Field(
        ...,
        description="Last date to exercise warrants"
    )

    # Optional Fields with Defaults
    warrant_trading_start: date = Field(
        default_factory=date.today,
        description="Date when warrant trading begins"
    )
    warrant_trading_end: date = Field(
        default_factory=date.today,
        description="Last date when warrants can be traded"
    )
    settlement_date: date = Field(
        default_factory=date.today,
        description="Date when exercised shares are delivered"
    )
    is_cashless_exercise: bool = Field(
        default=False,
        description="Whether exercise can be done without cash payment"
    )
    minimum_exercise_quantity: int = Field(
        default=1,
        gt=0,
        description="Minimum number of warrants that can be exercised at once"
    )

    # Valuation Fields with Defaults
    theoretical_warrant_value: condecimal(max_digits=20, decimal_places=6, ge=0) = Field(
        default=0,
        description="Theoretical value based on Black-Scholes"
    )
    warrant_trading_price: condecimal(max_digits=20, decimal_places=6, ge=0) = Field(
        default=0,
        description="Current market price of the warrant"
    )
    intrinsic_value: condecimal(max_digits=20, decimal_places=6, ge=0) = Field(
        default=0,
        description="Immediate exercise value"
    )
    time_value: condecimal(max_digits=20, decimal_places=6, ge=0) = Field(
        default=0,
        description="Value from remaining time until expiration"
    )

    # Metadata with Defaults
    warrant_terms: constr(max_length=5000, strip_whitespace=True) = Field(
        default="",
        description="Detailed terms and conditions"
    )
    exercise_notes: constr(max_length=2000, strip_whitespace=True) = Field(
        default="",
        description="Additional notes about the process"
    )

    @model_validator(mode='after')
    def validate_dates_chronology(self):
        if self.ex_warrant_date > self.exercise_deadline:
            raise ValueError("Ex-warrant date must be before exercise deadline")
        if self.warrant_trading_start > self.warrant_trading_end:
            raise ValueError("Warrant trading start must be before end date")
        if self.warrant_trading_end > self.exercise_deadline:
            raise ValueError("Warrant trading must end before exercise deadline")
        if self.exercise_deadline > self.settlement_date:
            raise ValueError("Exercise deadline must be before settlement date")
        return self

    model_config = ConfigDict(
        extra="forbid")


class WarrantExerciseResponse(CorporateActionResponse):
    exercise_price: float
    warrant_ratio: float
    exercise_ratio: float
    ex_warrant_date: date
    warrant_trading_start: date
    warrant_trading_end: date
    exercise_deadline: date
    settlement_date: date
    is_cashless_exercise: bool
    minimum_exercise_quantity: int
    theoretical_warrant_value: float
    warrant_trading_price: float
    intrinsic_value: float
    time_value: float
    warrant_terms: str
    exercise_notes: str
