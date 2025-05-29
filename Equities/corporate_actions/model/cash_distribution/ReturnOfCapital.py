from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class ReturnOfCapital(CorporateActionBase):
    __tablename__ = 'return_of_capital'
    API_Path = 'Return-Of-Capital'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Return of capital financial information
    return_amount = Column(NUMERIC(precision=20, scale=6), nullable=False)
    cost_basis_reduction = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Dates
    declaration_date = Column(Date, nullable=False)
    ex_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=False)

    # Impact on holdings
    affects_cost_basis = Column(Boolean, default=True, nullable=False)

    # Metadata
    return_reason = Column(Text, nullable=True)
    return_notes = Column(Text, nullable=True)
