from sqlalchemy import Column, Date, ForeignKey, Integer, NUMERIC, Text

from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from equity.src.model.corporate_actions.model.CorporateActionBase import CorporateActionBase


class ReverseSplit(CorporateActionBase):
    __tablename__ = 'reverse_split'
    __mapper_args__ = {
        'polymorphic_identity': CorporateActionTypeEnum.REVERSE_SPLIT.value
    }
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
