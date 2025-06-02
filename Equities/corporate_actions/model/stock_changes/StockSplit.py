from sqlalchemy import Column, Date, ForeignKey, Integer, NUMERIC, String, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class StockSplit(CorporateActionBase):
    __tablename__ = 'stock_split'
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

    # @validates('split_ratio_from', 'split_ratio_to')
    # def validate_ratios(self, key, value):
    #     if value is None or value <= 0:
    #         raise StockSplitValidationError(f"{key} must be positive")
    #     return value
    #
    # @validates('split_multiplier')
    # def validate_multiplier(self, key, value):
    #     if value is None or value <= 1:
    #         raise StockSplitValidationError("Split multiplier must be greater than 1")
    #     return value
    #
    # @validates('ex_split_date', 'effective_date')
    # def validate_dates(self, key, date_value):
    #     if date_value is None:
    #         raise StockSplitValidationError(f"{key} cannot be None")
    #     return date_value

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
