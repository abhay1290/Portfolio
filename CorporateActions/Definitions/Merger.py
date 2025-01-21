import datetime
from sqlalchemy import Column, DateTime, Integer, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from Database.database import Base


class Merger(Base):
    __tablename__ = 'mergers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), unique=True)

    company_a = Column(String, nullable=False)
    company_b = Column(String, nullable=False)
    record_date = Column(DateTime, nullable=False)
    payment_date = Column(DateTime, nullable=False)
    acquirer_price = Column(Numeric, nullable=False)
    target_price = Column(Numeric, nullable=False)
    premium_percent = Column(Numeric, nullable=False)

    # # Relationship back reference
    # corporate_action = relationship("CorporateAction", backref="mergers")

    def __init__(self, company_a, company_b, record_date: datetime, payment_date: datetime,
                 acquirer_price: float, target_price: float, premium_percent: float):
        self.company_a = company_a
        self.company_b = company_b
        self.record_date = record_date
        self.payment_date = payment_date
        self.acquirer_price = acquirer_price
        self.target_price = target_price
        self.premium_percent = premium_percent

    def calculate_prices(self):
        new_target_price = self.target_price * (1 + self.premium_percent / 100)
        new_acquirer_price = self.acquirer_price
        premium_paid = new_target_price - self.target_price

        return {
            "Company A": self.company_a,
            "Company B": self.company_b,
            "Record Date": self.record_date.strftime('%Y-%m-%d'),
            "Payment Date": self.payment_date.strftime('%Y-%m-%d'),
            "New Acquirer Price": round(new_acquirer_price, 2),
            "New Target Price": round(new_target_price, 2),
            "Premium Paid": round(premium_paid, 2)
        }