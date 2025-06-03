from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class SpecialDividend(CorporateActionBase):
    __tablename__ = 'special_dividend'
    API_Path = 'Special-Dividend'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Special dividend-specific financial information
    is_gross_dividend_amount = Column(Boolean, nullable=False, default=True)
    special_dividend_amount = Column(NUMERIC(precision=20, scale=6), nullable=False)
    eligible_outstanding_shares = Column(Float, nullable=False)

    # Special dividend-specific dates
    declaration_date = Column(Date, nullable=False)
    ex_dividend_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=False)

    # Dividend-specific tax information
    dividend_tax_rate = Column(Float, nullable=True)

    # Special dividend reason and metadata
    special_dividend_notes = Column(Text, nullable=True)

    # Calculated fields (populated during processing)
    net_special_dividend_amount = Column(NUMERIC(precision=20, scale=6), nullable=True)
    special_dividend_marketcap_in_dividend_currency = Column(NUMERIC(precision=20, scale=2), nullable=True)

    def calculate_net_dividend(self):
        """Calculate net special dividend amount after tax"""
        if self.is_taxable and self.dividend_tax_rate:
            tax_rate = self.dividend_tax_rate
        else:
            tax_rate = 0.0

        if self.is_gross_dividend_amount:
            self.net_special_dividend_amount = self.special_dividend_amount * (1 - tax_rate)
        else:
            self.net_special_dividend_amount = self.special_dividend_amount

        # Calculate total payout
        self.special_dividend_marketcap_in_dividend_currency = (
                self.net_special_dividend_amount * self.eligible_outstanding_shares)

    def __repr__(self):
        return (
            f"<SpecialDividend(id={self.corporate_action_id}, "
            f"amount={self.special_dividend_amount}, "
            f"payment_date='{self.payment_date}')>"
        )
