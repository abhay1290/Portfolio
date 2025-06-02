from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Distribution(CorporateActionBase):
    __tablename__ = 'distribution'
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

    #
    # @validates('distribution_amount')
    # def validate_distribution_amount(self, key: str, amount: float) -> float:
    #     try:
    #         amount = float(amount)
    #     except (TypeError, ValueError):
    #         raise DistributionValidationError("Distribution amount must be a number")
    #
    #     if amount <= 0:
    #         raise DistributionValidationError("Distribution amount must be positive")
    #     return amount
    #
    # @validates('eligible_outstanding_shares')
    # def validate_eligible_shares(self, key: str, eligible_shares: float) -> float:
    #     try:
    #         eligible_shares = float(eligible_shares)
    #     except (TypeError, ValueError):
    #         raise DistributionValidationError("Eligible outstanding shares must be a number")
    #
    #     if eligible_shares <= 0:
    #         raise DistributionValidationError("Eligible outstanding shares must be positive")
    #     return eligible_shares
    #
    # @validates('distribution_tax_rate')
    # def validate_tax_rates(self, key: str, tax_rate: Optional[float]) -> Optional[float]:
    #     if tax_rate is not None:
    #         try:
    #             tax_rate = float(tax_rate)
    #         except (TypeError, ValueError):
    #             raise DistributionValidationError("Tax rate must be a number")
    #
    #         if not (0.0 <= tax_rate <= 1.0):
    #             raise DistributionValidationError("Tax rate must be between 0.0 and 1.0")
    #     return tax_rate
    #
    # @validates('payment_date', 'declaration_date')
    # def validate_distribution_dates(self, key, date_value):
    #     if date_value is None:
    #         raise DistributionValidationError(f"{key} cannot be None")
    #     return date_value

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
