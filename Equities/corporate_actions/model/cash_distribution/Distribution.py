from sqlalchemy import Column, Date, ForeignKey, Integer, NUMERIC, String, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Distribution(CorporateActionBase):
    __tablename__ = 'distribution'
    API_Path = 'Distribution'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Distribution financial information
    distribution_amount = Column(NUMERIC(precision=20, scale=6), nullable=False)
    distribution_type = Column(String(100), nullable=False)  # e.g., "Capital Gain", "Interest"

    # Distribution dates
    declaration_date = Column(Date, nullable=False)
    ex_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=False)

    # Tax information
    taxable_amount = Column(NUMERIC(precision=20, scale=6), nullable=True)
    non_taxable_amount = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Metadata
    distribution_notes = Column(Text, nullable=True)
