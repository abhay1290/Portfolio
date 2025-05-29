from sqlalchemy import Column, Date, ForeignKey, Integer, NUMERIC, String, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class StockSplit(CorporateActionBase):
    __tablename__ = 'stock_split'
    API_Path = 'Stock-Split'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Split ratio information
    split_ratio_from = Column(Integer, nullable=False)  # Old shares
    split_ratio_to = Column(Integer, nullable=False)  # New shares
    split_multiplier = Column(NUMERIC(precision=10, scale=6), nullable=False)

    # Dates
    announcement_date = Column(Date, nullable=True)
    ex_split_date = Column(Date, nullable=False)
    effective_date = Column(Date, nullable=False)

    # Price adjustments
    price_adjustment_factor = Column(NUMERIC(precision=10, scale=6), nullable=True)

    # Fractional share handling
    cash_in_lieu_rate = Column(NUMERIC(precision=20, scale=6), nullable=True)
    fractional_share_treatment = Column(String(100), nullable=True)  # "CASH", "ROUND_UP", "ROUND_DOWN"

    # Metadata
    split_notes = Column(Text, nullable=True)
