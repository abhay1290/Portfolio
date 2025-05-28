from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from Currency.CurrencyEnum import CurrencyEnum
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from Equities.corporate_actions.enums.StatusEnum import StatusEnum


class CorporateActionBase(BaseModel):
    company_name: str
    action_type: CorporateActionTypeEnum
    record_date: datetime
    effective_date: datetime
    currency: CurrencyEnum
    status: StatusEnum
    details: Optional[str] = None


class CorporateActionCreate(CorporateActionBase):
    pass


class CorporateActionResponse(CorporateActionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
