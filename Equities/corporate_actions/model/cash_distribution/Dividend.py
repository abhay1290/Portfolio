from sqlalchemy import Column, Date, Enum, Float, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.enums.DividendFrequencyEnum import DividendFrequencyEnum
from Equities.corporate_actions.enums.TaxStatusEnum import TaxStatusEnum
from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Dividend(CorporateActionBase):
    __tablename__ = 'dividend'
    API_Path = 'Dividend'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Dividend-specific financial information
    dividend_amount = Column(NUMERIC(precision=20, scale=6), nullable=False)
    dividend_frequency = Column(Enum(DividendFrequencyEnum), nullable=True)
    gross_dividend = Column(NUMERIC(precision=20, scale=6), nullable=True)
    net_dividend = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Dividend-specific dates
    declaration_date = Column(Date, nullable=False)
    ex_dividend_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=False)

    # Dividend-specific tax information
    dividend_tax_status = Column(Enum(TaxStatusEnum), nullable=True)
    dividend_withholding_rate = Column(Float, nullable=True)

    # Derived metrics
    dividend_yield = Column(Float, nullable=True)

    # Additional metadata
    dividend_notes = Column(Text, nullable=True)

    # # Share structure
    # shares_outstanding = Column(Float, nullable=True)
    # float_shares = Column(Float, nullable=True)
    # market_cap = Column(Float, nullable=True)
