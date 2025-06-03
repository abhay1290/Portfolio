from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, NUMERIC, String, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Liquidation(CorporateActionBase):
    __tablename__ = 'liquidation'
    API_Path = 'Liquidation'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Liquidation details
    liquidation_type = Column(String(100), nullable=False)  # "Voluntary", "Involuntary", "Chapter7", "Chapter11"
    liquidation_value_per_share = Column(NUMERIC(precision=20, scale=6), nullable=False)
    priority_claims = Column(NUMERIC(precision=20, scale=6), nullable=True)  # Total claims with priority

    # Dates
    announcement_date = Column(Date, nullable=False)
    petition_date = Column(Date, nullable=True)  # For bankruptcies
    approval_date = Column(Date, nullable=True)
    effective_date = Column(Date, nullable=False)
    final_distribution_date = Column(Date, nullable=True)

    # Distribution details
    cash_distribution = Column(NUMERIC(precision=20, scale=6), nullable=True)
    asset_distribution_value = Column(NUMERIC(precision=20, scale=6), nullable=True)
    distribution_currency = Column(String(3), nullable=True)  # ISO currency code

    # Status tracking
    # liquidation_status = Column(Enum(LiquidationStatusEnum), nullable=False, default=LiquidationStatusEnum.PENDING)
    is_complete = Column(Boolean, default=False, nullable=False)

    # Recovery rates
    estimated_recovery_rate = Column(NUMERIC(precision=10, scale=6), nullable=True)  # 0-1 scale
    actual_recovery_rate = Column(NUMERIC(precision=10, scale=6), nullable=True)  # 0-1 scale

    # Metadata
    liquidation_reason = Column(Text, nullable=True)
    liquidation_notes = Column(Text, nullable=True)

    def calculate_recovery_rate(self, key, face_value):
        """Calculate recovery rate based on distributions"""
        if face_value and face_value > 0 and self.cash_distribution is not None:
            total_distribution = self.cash_distribution
            if self.asset_distribution_value is not None:
                total_distribution += self.asset_distribution_value
            self.actual_recovery_rate = total_distribution / face_value

    def __repr__(self):
        return (
            f"<Liquidation(id={self.corporate_action_id}, "
            f"type='{self.liquidation_type}', "
            f"value={self.liquidation_value_per_share})>"
        )
