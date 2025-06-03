from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Numeric, Text

from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from equity.src.model.corporate_actions.model.CorporateActionBase import CorporateActionBase


class WarrantExercise(CorporateActionBase):
    __tablename__ = 'warrant_exercise'
    __mapper_args__ = {
        'polymorphic_identity': CorporateActionTypeEnum.WARRANT_EXERCISE.value
    }
    API_Path = 'Warrant-Exercise'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Required fields
    exercise_price = Column(Numeric(precision=20, scale=6), nullable=False)
    warrant_ratio = Column(Numeric(precision=10, scale=6), nullable=False)
    exercise_ratio = Column(Numeric(precision=10, scale=6), nullable=False)
    ex_warrant_date = Column(Date, nullable=False)
    exercise_deadline = Column(Date, nullable=False)

    # Optional fields with defaults
    warrant_trading_start = Column(Date, nullable=False, default=date.today)
    warrant_trading_end = Column(Date, nullable=False, default=date.today)
    settlement_date = Column(Date, nullable=False, default=date.today)
    is_cashless_exercise = Column(Boolean, nullable=False, default=False)
    minimum_exercise_quantity = Column(Integer, nullable=False, default=1)

    # Valuation fields with defaults
    theoretical_warrant_value = Column(Numeric(precision=20, scale=6), nullable=False, default=0)
    warrant_trading_price = Column(Numeric(precision=20, scale=6), nullable=False, default=0)
    intrinsic_value = Column(Numeric(precision=20, scale=6), nullable=False, default=0)
    time_value = Column(Numeric(precision=20, scale=6), nullable=False, default=0)

    # Metadata with defaults
    warrant_terms = Column(Text, nullable=False, default='')
    exercise_notes = Column(Text, nullable=False, default='')

    def calculate_theoretical_warrant_value(self, market_price: float) -> None:
        """Calculate theoretical warrant value"""
        if market_price and self.exercise_price and self.warrant_ratio:
            cum_warrant_price = Decimal(str(market_price))
            ex_warrant_price = (cum_warrant_price + (
                    Decimal(str(self.exercise_price)) / Decimal(str(self.warrant_ratio)))) / (
                                       1 + (1 / Decimal(str(self.warrant_ratio))))
            self.theoretical_warrant_value = float(cum_warrant_price - ex_warrant_price)

    def calculate_intrinsic_value(self, market_price: float) -> None:
        """Calculate intrinsic value (immediate exercise value)"""
        if market_price and self.exercise_price and self.exercise_ratio:
            intrinsic = max(0, (Decimal(str(market_price)) - Decimal(str(self.exercise_price))) * Decimal(
                str(self.exercise_ratio)))
            self.intrinsic_value = float(intrinsic)

    def __repr__(self):
        return (
            f"<WarrantExercise(id={self.corporate_action_id}, "
            f"exercise_price={self.exercise_price}, "
            f"expiration='{self.exercise_deadline}')>"
        )
