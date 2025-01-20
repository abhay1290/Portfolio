import datetime
from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from Database.database2 import Base


class CashDividend(Base):
    __tablename__ = 'cash_dividend'

    id = Column(Integer, primary_key=True, autoincrement=True)
    corporate_action_id = Column(Integer, ForeignKey('corporate_action.action_id'), unique=True)

    dividend_amount = Column(Numeric, nullable=False)
    declaration_date = Column(DateTime, nullable=False)
    ex_dividend_date = Column(DateTime, nullable=False)
    record_date = Column(DateTime, nullable=False)
    payment_date = Column(DateTime, nullable=False)

    # Relationship back reference
    corporate_action = relationship("CorporateAction", backref="cash_dividend")


    def __init__(self, dividend_amount, declaration_date: datetime,
                 record_date: datetime, payment_date: datetime,
                 ex_dividend_date:datetime):

        self.dividend_amount = dividend_amount
        self.declaration_date = declaration_date
        self.ex_dividend_date = ex_dividend_date
        self.record_date = record_date
        self.payment_date = payment_date



    def __repr__(self):
        return f"<CashDividend(dividend_amount={self.dividend_amount}, " \
               f"declaration_date={self.declaration_date}, " \
               f"ex_dividend_date={self.ex_dividend_date}, " \
               f"record_date={self.record_date}, " \
               f"payment_date={self.payment_date})>"


