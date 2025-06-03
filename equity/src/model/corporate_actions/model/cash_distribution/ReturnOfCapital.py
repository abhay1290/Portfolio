from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, NUMERIC, Text

from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from equity.src.model.corporate_actions.model.CorporateActionBase import CorporateActionBase


class ReturnOfCapital(CorporateActionBase):
    __tablename__ = 'return_of_capital'
    __mapper_args__ = {
        'polymorphic_identity': CorporateActionTypeEnum.RETURN_OF_CAPITAL.value
    }
    API_Path = 'Return-Of-Capital'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Return of capital financial information
    return_amount = Column(NUMERIC(precision=20, scale=6), nullable=False)
    eligible_outstanding_shares = Column(NUMERIC(precision=20, scale=6), nullable=False)
    cost_basis_reduction = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Dates
    declaration_date = Column(Date, nullable=False)
    ex_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=False)

    # Impact on holdings
    affects_cost_basis = Column(Boolean, default=True, nullable=False)
    tax_rate = Column(NUMERIC(precision=6, scale=4), nullable=True)

    # Metadata
    return_notes = Column(Text, nullable=True)

    # Calculated fields (populated during processing)
    total_return_amount = Column(NUMERIC(precision=20, scale=6), nullable=True)
    total_cost_basis_reduction = Column(NUMERIC(precision=20, scale=6), nullable=True)


def calculate_total_return(self):
    """Calculate total return amount and cost basis reduction"""
    self.total_return_amount = self.return_amount * self.eligible_outstanding_shares

    if self.affects_cost_basis and self.cost_basis_reduction:
        self.total_cost_basis_reduction = self.cost_basis_reduction * self.eligible_outstanding_shares
    else:
        self.total_cost_basis_reduction = 0


def __repr__(self):
    return (
        f"<ReturnOfCapital(id={self.corporate_action_id},"
        f" amount={self.return_amount},"
        f" payment_date='{self.payment_date}')>"
    )
