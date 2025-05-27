from datetime import date

from pydantic import BaseModel, Field


class CallScheduleEntry(BaseModel):
    date: date
    price: float = Field(..., ge=0)
