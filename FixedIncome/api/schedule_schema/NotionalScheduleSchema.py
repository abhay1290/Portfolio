from datetime import date

from pydantic import BaseModel, Field


class NotionalScheduleEntry(BaseModel):
    sinking_date: date
    notional: float = Field(..., ge=0)
