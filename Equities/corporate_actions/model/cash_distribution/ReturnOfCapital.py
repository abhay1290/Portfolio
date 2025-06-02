from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class ReturnOfCapital(CorporateActionBase):
    __tablename__ = 'return_of_capital'
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


#
# @validates('return_amount')
# def validate_return_amount(self, key, return_amount):
#     if return_amount is None or return_amount <= 0:
#         raise ReturnOfCapitalValidationError("Return amount must be positive")
#     return return_amount
#
#
# @validates('eligible_outstanding_shares')
# def validate_eligible_shares(self, key, eligible_shares):
#     if eligible_shares is None or eligible_shares <= 0:
#         raise ReturnOfCapitalValidationError("Eligible outstanding shares must be positive")
#     return eligible_shares
#
#
# @validates('tax_rate')
# def validate_tax_rate(self, key, tax_rate):
#     if tax_rate is not None and not (0 <= tax_rate <= 1):
#         raise ReturnOfCapitalValidationError("Tax rate must be between 0 and 1")
#     return tax_rate
#
#
# @validates('payment_date', 'declaration_date', 'record_date')
# def validate_dates(self, key, date_value):
#     if date_value is None:
#         raise ReturnOfCapitalValidationError(f"{key} cannot be None")
#     return date_value


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
