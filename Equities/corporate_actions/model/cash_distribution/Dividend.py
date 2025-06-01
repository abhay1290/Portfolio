from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, NUMERIC, Text
from sqlalchemy.orm import validates

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Dividend(CorporateActionBase):
    __tablename__ = 'dividend'
    API_Path = 'Dividend'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Dividend-specific financial information
    is_gross_dividend_amount = Column(Boolean, nullable=False, default=True)
    dividend_amount = Column(NUMERIC(precision=20, scale=6), nullable=False)
    eligible_outstanding_shares = Column(Float, nullable=False)

    # Dividend-specific dates
    declaration_date = Column(Date, nullable=False)
    ex_dividend_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=False)

    # Dividend-specific tax information
    dividend_tax_rate = Column(Float, nullable=True)

    # Additional metadata
    dividend_notes = Column(Text, nullable=True)

    # Calculated fields (populated during processing)
    net_dividend_amount = Column(NUMERIC(precision=20, scale=6), nullable=True)
    dividend_marketcap_dividend_currency = Column(NUMERIC(precision=20, scale=2), nullable=True)

    @validates('dividend_amount')
    def validate_dividend_amount(self, key, dividend_amount):
        if dividend_amount is None or dividend_amount <= 0:
            raise DividendValidationError("Dividend amount must be positive")
        return dividend_amount

    @validates('eligible_outstanding_shares')
    def validate_eligible_shares(self, key, eligible_shares):
        if eligible_shares is None or eligible_shares <= 0:
            raise DividendValidationError("Eligible outstanding shares must be positive")
        return eligible_shares

    @validates('dividend_tax_rate')
    def validate_tax_rates(self, key, tax_rate):
        if tax_rate is not None and not (0.0 <= tax_rate <= 1.0):
            raise DividendValidationError(f"{key} must be between 0.0 and 1.0")
        return tax_rate

    @validates('payment_date', 'declaration_date')
    def validate_dividend_dates(self, key, date_value):
        if date_value is None:
            raise DividendValidationError(f"{key} cannot be None")
        return date_value

    def calculate_net_dividend(self):
        """Calculate net dividend amount after tax"""
        if self.is_taxable and self.dividend_tax_rate:
            tax_rate = self.dividend_tax_rate
        else:
            tax_rate = 0.0

        if self.is_gross_dividend_amount:
            self.net_dividend_amount = self.dividend_amount * (1 - tax_rate)
        else:
            self.net_dividend_amount = self.dividend_amount

        # Calculate total payout
        self.dividend_marketcap_dividend_currency = self.net_dividend_amount * self.eligible_outstanding_shares

    def __repr__(self):
        return f"<Dividend(id={self.corporate_action_id}, amount={self.dividend_amount}, payment_date='{self.payment_date}')>"
