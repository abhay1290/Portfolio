from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, NUMERIC, Text

from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from equity.src.model.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Distribution(CorporateActionBase):
    __tablename__ = 'distribution'
    __mapper_args__ = {
        'polymorphic_identity': CorporateActionTypeEnum.DISTRIBUTION.value
    }
    API_Path = 'Distribution'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Distribution-specific financial information
    is_gross_distribution_amount = Column(Boolean, nullable=False, default=True)
    distribution_amount = Column(NUMERIC(precision=20, scale=6), nullable=False)
    eligible_outstanding_shares = Column(Float, nullable=False)

    # Distribution-specific dates
    declaration_date = Column(Date, nullable=False)
    ex_distribution_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=False)

    # Distribution-specific tax information
    distribution_tax_rate = Column(Float, nullable=True)
    taxable_amount = Column(NUMERIC(precision=20, scale=6), nullable=True)
    non_taxable_amount = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Additional metadata
    distribution_notes = Column(Text, nullable=True)

    # Calculated fields (populated during processing)
    net_distribution_amount = Column(NUMERIC(precision=20, scale=6), nullable=True)
    total_distribution_payout = Column(NUMERIC(precision=20, scale=2), nullable=True)

    def calculate_net_distribution(self):
        """Calculate net distribution amount after tax"""
        if self.is_taxable and self.distribution_tax_rate:
            tax_rate = self.distribution_tax_rate
        else:
            tax_rate = 0.0

        if self.is_gross_distribution_amount:
            self.net_distribution_amount = self.distribution_amount * (1 - tax_rate)
        else:
            self.net_distribution_amount = self.distribution_amount

        # Calculate total payout
        self.total_distribution_payout = self.net_distribution_amount * self.eligible_outstanding_shares

    def __repr__(self):
        return (
            f"<Distribution(id={self.corporate_action_id}, "
            f"amount={self.distribution_amount}, "
            f"type='{self.distribution_type}', "
            f"payment_date='{self.payment_date}')>"
        )
