from sqlalchemy import Column, Date, ForeignKey, Integer, NUMERIC, Text
from sqlalchemy.orm import validates

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase
from Equities.utils.Exceptions import ReverseSplitValidationError


class ReverseSplit(CorporateActionBase):
    __tablename__ = 'reverse_split'
    API_Path = 'Reverse-Split'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

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

    @validates('reverse_ratio_from', 'reverse_ratio_to')
    def validate_ratios(self, key, value):
        if value is None or value <= 0:
            raise ReverseSplitValidationError(f"{key} must be positive")
        return value

    @validates('reverse_multiplier')
    def validate_multiplier(self, value):
        if value is None or value <= 0 or value >= 1:
            raise ReverseSplitValidationError("Reverse multiplier must be between 0 and 1")
        return value

    @validates('ex_split_date', 'effective_date')
    def validate_dates(self, key, date_value):
        if date_value is None:
            raise ReverseSplitValidationError(f"{key} cannot be None")
        return date_value

    def calculate_reverse_multiplier(self):
        """Calculate reverse split multiplier"""
        if self.reverse_ratio_from and self.reverse_ratio_to:
            self.reverse_multiplier = self.reverse_ratio_to / self.reverse_ratio_from
            self.price_adjustment_factor = self.reverse_ratio_from / self.reverse_ratio_to

    def __repr__(self):
        return (
            f"<ReverseSplit(id={self.corporate_action_id}, "
            f"ratio={self.reverse_ratio_from}:{self.reverse_ratio_to}, "
            f"ex_date='{self.ex_split_date}')>"
        )
