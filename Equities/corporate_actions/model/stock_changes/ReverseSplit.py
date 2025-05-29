from sqlalchemy import Column, Date, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class ReverseSplit(CorporateActionBase):
    __tablename__ = 'reverse_split'
    API_Path = 'Reverse-Split'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Reverse split ratio information
    reverse_ratio_from = Column(Integer, nullable=False)  # Old shares (higher number)
    reverse_ratio_to = Column(Integer, nullable=False)  # New shares (lower number)
    reverse_multiplier = Column(NUMERIC(precision=10, scale=6), nullable=False)

    # Dates
    announcement_date = Column(Date, nullable=True)
    ex_split_date = Column(Date, nullable=False)
    effective_date = Column(Date, nullable=False)

    # Price adjustments
    price_adjustment_factor = Column(NUMERIC(precision=10, scale=6), nullable=True)

    # Fractional share handling
    cash_in_lieu_rate = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Metadata
    reverse_split_reason = Column(Text, nullable=True)
    reverse_split_notes = Column(Text, nullable=True)
