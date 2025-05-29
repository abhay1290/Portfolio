from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, NUMERIC, String, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Liquidation(CorporateActionBase):
    __tablename__ = 'liquidation'
    API_Path = 'Liquidation'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Liquidation details
    liquidation_type = Column(String(100), nullable=False)  # "Voluntary", "Involuntary"
    liquidation_value_per_share = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Dates
    liquidation_announcement_date = Column(Date, nullable=True)
    liquidation_effective_date = Column(Date, nullable=False)
    final_distribution_date = Column(Date, nullable=True)

    # Distribution details
    cash_distribution = Column(NUMERIC(precision=20, scale=6), nullable=True)
    asset_distribution_value = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Status
    is_complete = Column(Boolean, default=False, nullable=False)

    # Metadata
    liquidation_reason = Column(Text, nullable=True)
    liquidation_notes = Column(Text, nullable=True)
