from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Delisting(CorporateActionBase):
    __tablename__ = 'delisting'
    API_Path = 'Delisting'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Delisting details
    delisting_reason = Column(String(255), nullable=False)
    is_voluntary = Column(Boolean, default=False, nullable=False)
    final_trading_date = Column(Date, nullable=False)

    # New trading venue (if applicable)
    new_exchange = Column(String(100), nullable=True)
    new_symbol = Column(String(20), nullable=True)

    # Dates
    notification_date = Column(Date, nullable=True)
    effective_date = Column(Date, nullable=False)

    # Impact on shareholders
    shareholder_impact = Column(Text, nullable=True)
    delisting_notes = Column(Text, nullable=True)
