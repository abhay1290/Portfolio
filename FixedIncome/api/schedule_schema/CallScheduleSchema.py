from datetime import date

from pydantic import BaseModel, Field


class CallScheduleEntry(BaseModel):
    call_date: date
    call_price: float = Field(..., ge=0)
