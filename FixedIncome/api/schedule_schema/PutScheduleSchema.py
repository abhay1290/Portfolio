from datetime import date

from pydantic import BaseModel, Field


class PutScheduleEntry(BaseModel):
    put_date: date
    put_price: float = Field(..., ge=0)
