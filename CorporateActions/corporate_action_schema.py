from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from CorporateActions.CorporateActionEnum import CorporateActionEnum
from CorporateActions.StatusEnum import StatusEnum
from Currency.CurrencyEnum import CurrencyEnum
from Identifier.AssetClassEnum import AssetClassEnum

class CorporateActionBase(BaseModel):
    company_name: str
    action_type: CorporateActionEnum
    record_date: datetime
    effective_date: datetime
    currency: CurrencyEnum
    status: StatusEnum
    details: Optional[str] = None


class CorporateActionCreate(CorporateActionBase):
    pass

class CorporateActionResponse(CorporateActionBase):
    id: int

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, obj):
        return cls.model_validate(obj)
