from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, Numeric, Text

from Equities.corporate_actions.enums.DividendFrequencyEnum import DividendFrequencyEnum
from Equities.corporate_actions.enums.DividendTypeEnum import DividendTypeEnum
from Equities.corporate_actions.enums.TaxStatusEnum import TaxStatusEnum
from Equities.corporate_actions.model.CorporateAction import CorporateAction


class Dividend(CorporateAction):
    __tablename__ = 'dividend'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Financial Dividend Info
    dividend_type = Column(Enum(DividendTypeEnum), nullable=False)
    dividend_amount = Column(Numeric(precision=20, scale=6), nullable=False)
    dividend_frequency = Column(Enum(DividendFrequencyEnum), nullable=True)

    # Key Dates
    declaration_date = Column(DateTime, nullable=False)
    ex_dividend_date = Column(DateTime, nullable=True)
    payment_date = Column(DateTime, nullable=False)

    # Additional Metadata
    tax_status = Column(Enum(TaxStatusEnum), nullable=True)
    gross_dividend = Column(Numeric(precision=20, scale=6), nullable=True)
    net_dividend = Column(Numeric(precision=20, scale=6), nullable=True)
    withholding_tax_rate = Column(Float, nullable=True)

    # Derived/Optional
    dividend_yield = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    # # Share structure
    # shares_outstanding = Column(Float, nullable=True)
    # float_shares = Column(Float, nullable=True)
    # market_cap = Column(Float, nullable=True)
