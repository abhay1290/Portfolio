from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, NUMERIC, String, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Acquisition(CorporateActionBase):
    __tablename__ = 'acquisition'
    API_Path = 'Acquisition'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Acquisition details
    acquiring_company_id = Column(Integer, ForeignKey('equity.id'), nullable=True)
    acquisition_price = Column(NUMERIC(precision=20, scale=6), nullable=False)
    acquisition_premium = Column(Float, nullable=True)
    shares_exchanged = Column(NUMERIC(precision=20, scale=6), nullable=True)  # For stock acquisitions
    exchange_ratio = Column(Float, nullable=True)  # For stock acquisitions

    # Dates
    announcement_date = Column(Date, nullable=False)
    expected_completion_date = Column(Date, nullable=False)
    completion_date = Column(Date, nullable=True)  # Populated when completed

    # Transaction details
    acquisition_method = Column(String(100), nullable=False)  # "CASH", "STOCK", "MIXED"
    is_friendly = Column(Boolean, default=True, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)

    # Financial impact
    premium_over_market = Column(Float, nullable=True)

    # Metadata
    acquisition_notes = Column(Text, nullable=True)

    # Calculated fields (populated during processing)
    total_acquisition_value = Column(NUMERIC(precision=20, scale=6), nullable=True)
    implied_equity_value = Column(NUMERIC(precision=20, scale=6), nullable=True)


def calculate_total_value(self):
    """Calculate total acquisition value and implied equity value"""
    if self.acquisition_method == 'CASH':
        self.total_acquisition_value = self.acquisition_price * self.equity.shares_outstanding
    elif self.acquisition_method == 'STOCK' and self.exchange_ratio:
        self.total_acquisition_value = self.acquisition_price * self.equity.shares_outstanding
        self.shares_exchanged = self.equity.shares_outstanding * self.exchange_ratio
    elif self.acquisition_method == 'MIXED':
        # Implement mixed consideration logic
        pass

    self.implied_equity_value = self.total_acquisition_value


def mark_completed(self, actual_completion_date):
    """Mark the acquisition as completed"""
    self.completion_date = actual_completion_date
    self.is_completed = True


def __repr__(self):
    return (f"<Acquisition(id={self.corporate_action_id}, "
            f"price={self.acquisition_price}, "
            f"method='{self.acquisition_method}', "
            f"completed={self.is_completed})>")
