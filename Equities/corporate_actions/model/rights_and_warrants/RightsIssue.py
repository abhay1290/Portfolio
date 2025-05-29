from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.enums.RightsStatusEnum import RightsStatusEnum
from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class RightsIssue(CorporateActionBase):
    __tablename__ = 'rights_issue'
    API_Path = 'Rights-Issue'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Rights details
    subscription_price = Column(NUMERIC(precision=20, scale=6), nullable=False)
    rights_ratio = Column(NUMERIC(precision=10, scale=6), nullable=False)  # Rights per share held
    subscription_ratio = Column(NUMERIC(precision=10, scale=6), nullable=False)  # New shares per right

    # Dates
    announcement_date = Column(Date, nullable=True)
    ex_rights_date = Column(Date, nullable=False)
    rights_trading_start = Column(Date, nullable=True)
    rights_trading_end = Column(Date, nullable=True)
    subscription_deadline = Column(Date, nullable=False)

    # Rights valuation
    theoretical_rights_value = Column(NUMERIC(precision=20, scale=6), nullable=True)
    rights_trading_price = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Status tracking
    rights_status = Column(Enum(RightsStatusEnum), nullable=False, default=RightsStatusEnum.ACTIVE)

    # Metadata
    rights_purpose = Column(Text, nullable=True)  # Why rights were issued
    rights_notes = Column(Text, nullable=True)
