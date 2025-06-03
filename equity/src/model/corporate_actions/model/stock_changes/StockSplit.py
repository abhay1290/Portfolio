from sqlalchemy import Column, Date, ForeignKey, Integer, NUMERIC, String, Text

from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from equity.src.model.corporate_actions.model.CorporateActionBase import CorporateActionBase


class StockSplit(CorporateActionBase):
    __tablename__ = 'stock_split'
    __mapper_args__ = {
        'polymorphic_identity': CorporateActionTypeEnum.STOCK_SPLIT.value
    }
    API_Path = 'Stock-Split'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

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
    fractional_share_treatment = Column(String(100), nullable=True)

    # Metadata
    split_notes = Column(Text, nullable=True)

    def calculate_split_multiplier(self):
        """Calculate split multiplier"""
        if self.split_ratio_from and self.split_ratio_to:
            self.split_multiplier = self.split_ratio_to / self.split_ratio_from
            self.price_adjustment_factor = self.split_ratio_from / self.split_ratio_to

    def __repr__(self):
        return (
            f"<StockSplit(id={self.corporate_action_id}, "
            f"ratio={self.split_ratio_from}:{self.split_ratio_to}, "
            f"ex_date='{self.ex_split_date}')>"
        )
