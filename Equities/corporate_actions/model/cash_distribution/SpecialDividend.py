from sqlalchemy import Column, Date, Enum, Float, ForeignKey, Integer, NUMERIC, String, Text

from Equities.corporate_actions.enums.TaxStatusEnum import TaxStatusEnum
from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class SpecialDividend(CorporateActionBase):
    __tablename__ = 'special_dividend'
    API_Path = 'Special-Dividend'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Special dividend-specific financial information
    special_dividend_amount = Column(NUMERIC(precision=20, scale=6), nullable=False)
    gross_amount = Column(NUMERIC(precision=20, scale=6), nullable=True)
    net_amount = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Special dividend-specific dates
    declaration_date = Column(Date, nullable=False)
    ex_dividend_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=False)

    # Tax information
    withholding_rate = Column(Float, nullable=True)
    tax_status = Column(Enum(TaxStatusEnum), nullable=True)

    # Special dividend reason and metadata
    dividend_reason = Column(Text, nullable=True)
    dividend_source = Column(String(255), nullable=True)  # e.g., "Asset Sale", "Capital Gain"
    special_dividend_notes = Column(Text, nullable=True)
