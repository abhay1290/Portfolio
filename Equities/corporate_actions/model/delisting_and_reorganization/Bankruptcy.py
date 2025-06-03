from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Bankruptcy(CorporateActionBase):
    __tablename__ = 'bankruptcy'
    API_Path = 'Bankruptcy'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

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

    # Calculated fields
    estimated_recovery_value = Column(Float, nullable=True)

    # Metadata
    court_jurisdiction = Column(String(255), nullable=True)
    bankruptcy_notes = Column(Text, nullable=True)


def calculate_recovery_value(self, key, equity_value):
    """Calculate estimated recovery value based on equity value"""
    if self.estimated_recovery_rate is not None:
        self.estimated_recovery_value = equity_value * self.estimated_recovery_rate
    return self.estimated_recovery_value


def mark_completed(self, suspension_date):
    """Mark the equity as trading suspended"""
    self.trading_suspension_date = suspension_date
    self.is_trading_suspended = True


def __repr__(self):
    return (f"<Bankruptcy(id={self.corporate_action_id}, "
            f"type='{self.bankruptcy_type}', "
            f"filing_date={self.filing_date}, "
            f"recovery_rate={self.estimated_recovery_rate})>")
