from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, NUMERIC, String, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Reorganization(CorporateActionBase):
    __tablename__ = 'reorganization'
    API_Path = 'Reorganization'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Reorganization details
    reorganization_type = Column(String(100), nullable=False)
    new_entity_id = Column(Integer, ForeignKey('equity.id'), nullable=True)

    # Exchange terms
    exchange_ratio = Column(NUMERIC(precision=10, scale=6), nullable=True)
    cash_component = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Dates
    announcement_date = Column(Date, nullable=True)
    shareholder_approval_date = Column(Date, nullable=True)
    effective_date = Column(Date, nullable=False)

    # Tax implications
    is_tax_free = Column(Boolean, default=False, nullable=False)

    # Metadata
    reorganization_purpose = Column(Text, nullable=True)
    reorganization_notes = Column(Text, nullable=True)
