from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime

from CorporateActions.CorporateActionEnum import CorporateActionEnum
from CorporateActions.StatusEnum import StatusEnum
from Currency.CurrencyEnum import CurrencyEnum

from Database.database import Base


class CorporateAction(Base):
    __tablename__ = 'corporate_action'

    id = Column(Integer, primary_key=True, autoincrement=True)

    company_name = Column(String, nullable=False)
    action_type = Column(Enum(CorporateActionEnum), nullable=False)
    record_date = Column(DateTime, nullable=False)
    effective_date = Column(DateTime, nullable=False)
    currency = Column(Enum(CurrencyEnum), nullable=False)
    status = Column(Enum(StatusEnum), nullable=False)
    details = Column(String, nullable=False)

    # Define relationship back to Equity, allowing the action to be optional
    # ca = relationship("Equity", back_populates="corporate_actions", uselist=False)
    # equity_id = Column(Integer, ForeignKey('ca.id'))

    def __init__(self, company_name: str, action_type: CorporateActionEnum, record_date: datetime,
                 effective_date: datetime, currency: CurrencyEnum, status: StatusEnum, details: str):

        self.company_name = company_name
        self.action_type = action_type
        self.record_date = record_date
        self.effective_date = effective_date
        self.currency = currency
        self.status = status
        self.details = details

    def announce_action(self):
        """Announce a new corporate action."""
        print(f"Corporate Action '{self.action_type}' announced by {self.company_name}.")
        print(f"Record Date: {self.record_date}, Effective Date: {self.effective_date}")
        print(f"Details: {self.details} in {self.currency}")
        self.status = "Announced"

    def update_status(self, new_status):
        """Update the status of the corporate action."""
        self.status = new_status
        print(f"Status of corporate action '{self.action_type}' has been updated to {self.status}.")

    def get_action_summary(self):
        """Return a summary of the corporate action details."""
        return {
            'ID': self.id,
            'Company': self.company_name,
            'Type': self.action_type,
            'Record Date': self.record_date,
            'Effective Date': self.effective_date,
            'Details': self.details,
            'Currency': self.currency,
            'Status': self.status
        }

