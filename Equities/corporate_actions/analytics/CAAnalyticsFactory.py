from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


def bond_analytics_factory(ca: CorporateActionBase):
    if ca.action_type == CorporateActionTypeEnum.DIVIDEND or ca.action_type == CorporateActionTypeEnum.SPECIAL_DIVIDEND:
        pass
    elif ca.action_type == CorporateActionTypeEnum.STOCK_SPLIT:
        pass
    else:
        raise ValueError(f"Unsupported corporate action type: {ca.action_type}")
