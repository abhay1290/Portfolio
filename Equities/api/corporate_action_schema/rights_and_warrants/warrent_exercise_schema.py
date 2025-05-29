# Corporate Action Pydantic Request/Response Models
from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field
from pydantic.types import condecimal, constr

from Equities.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, CorporateActionResponse
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class WarrantExerciseRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(CorporateActionTypeEnum.WARRANT_EXERCISE)

    # Warrant Details
    exercise_price: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0)
    exercise_ratio: condecimal(max_digits=10, decimal_places=6) = Field(..., gt=0)

    # Key Dates
    expiration_date: date = Field(..., description="Warrant expiration date")
    exercise_deadline: date = Field(..., description="Exercise deadline")
    settlement_date: Optional[date] = Field(None)

    # Exercise Conditions
    is_cashless_exercise: bool = Field(default=False)
    minimum_exercise_quantity: Optional[int] = Field(None, gt=0)

    # Valuation
    intrinsic_value: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)
    time_value: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)

    # Additional Information
    warrant_terms: Optional[constr(max_length=5000)] = Field(None)
    exercise_notes: Optional[constr(max_length=2000)] = Field(None)

    model_config = ConfigDict(extra="forbid")


class WarrantExerciseResponse(CorporateActionResponse):
    exercise_price: float
    exercise_ratio: float
    expiration_date: date
    exercise_deadline: date
    settlement_date: Optional[date] = None
    is_cashless_exercise: bool
    minimum_exercise_quantity: Optional[int] = None
    intrinsic_value: Optional[float] = None
    time_value: Optional[float] = None
    warrant_terms: Optional[str] = None
    exercise_notes: Optional[str] = None
