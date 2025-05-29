from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Bankruptcy(CorporateActionBase):
    __tablename__ = 'bankruptcy'
    API_Path = 'Bankruptcy'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Bankruptcy details
    bankruptcy_type = Column(String(50), nullable=False)  # "Chapter 7", "Chapter 11", etc.
    filing_date = Column(Date, nullable=False)

    # Recovery estimates
    estimated_recovery_rate = Column(Float, nullable=True)
    recovery_timeline = Column(String(255), nullable=True)

    # Dates
    court_approval_date = Column(Date, nullable=True)
    plan_effective_date = Column(Date, nullable=True)

    # Impact
    trading_suspension_date = Column(Date, nullable=True)
    is_trading_suspended = Column(Boolean, default=True, nullable=False)

    # Metadata
    court_jurisdiction = Column(String(255), nullable=True)
    bankruptcy_notes = Column(Text, nullable=True)
