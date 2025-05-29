from sqlalchemy import Boolean, Column, Date, Enum, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.enums.MergerTypeEnum import MergerTypeEnum
from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Merger(CorporateActionBase):
    __tablename__ = 'merger'
    API_Path = 'Merger'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Merger details
    acquiring_company_id = Column(Integer, ForeignKey('equity.id'), nullable=True)
    merger_type = Column(Enum(MergerTypeEnum), nullable=False)

    # Consideration details
    cash_consideration = Column(NUMERIC(precision=20, scale=6), nullable=True)
    stock_consideration_ratio = Column(NUMERIC(precision=10, scale=6), nullable=True)
    total_consideration_value = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Dates
    announcement_date = Column(Date, nullable=True)
    shareholder_approval_date = Column(Date, nullable=True)
    effective_date = Column(Date, nullable=False)

    # Tax implications
    is_tax_free_reorganization = Column(Boolean, default=False, nullable=False)
    taxable_gain_recognition = Column(Boolean, default=True, nullable=False)

    # Metadata
    merger_terms = Column(Text, nullable=True)
    merger_notes = Column(Text, nullable=True)
