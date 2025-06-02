from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class WarrantExercise(CorporateActionBase):
    __tablename__ = 'warrant_exercise'
    API_Path = 'Warrant-Exercise'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Warrant details
    exercise_price = Column(NUMERIC(precision=20, scale=6), nullable=False)
    warrant_ratio = Column(NUMERIC(precision=10, scale=6), nullable=False)  # Warrants per share
    exercise_ratio = Column(NUMERIC(precision=10, scale=6), nullable=False)  # Shares per warrant

    # Dates
    announcement_date = Column(Date, nullable=True)
    ex_warrant_date = Column(Date, nullable=False)
    warrant_trading_start = Column(Date, nullable=True)
    warrant_trading_end = Column(Date, nullable=True)
    exercise_deadline = Column(Date, nullable=False)
    settlement_date = Column(Date, nullable=True)

    # Exercise conditions
    is_cashless_exercise = Column(Boolean, default=False, nullable=False)
    minimum_exercise_quantity = Column(Integer, nullable=True)

    # Valuation
    theoretical_warrant_value = Column(NUMERIC(precision=20, scale=6), nullable=True)
    warrant_trading_price = Column(NUMERIC(precision=20, scale=6), nullable=True)
    intrinsic_value = Column(NUMERIC(precision=20, scale=6), nullable=True)
    time_value = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Status tracking
    # warrant_status = Column(Enum(WarrantStatusEnum), nullable=False, default=WarrantStatusEnum.ACTIVE)

    # Metadata
    warrant_terms = Column(Text, nullable=True)
    exercise_notes = Column(Text, nullable=True)

    #
    # @validates('exercise_price')
    # def validate_exercise_price(self, key, value):
    #     if value is None or value <= 0:
    #         raise WarrantValidationError("Exercise price must be positive")
    #     return value
    #
    # @validates('warrant_ratio', 'exercise_ratio')
    # def validate_ratios(self, key, value):
    #     if value is None or value <= 0:
    #         raise WarrantValidationError(f"{key} must be positive")
    #     return value
    #
    # @validates('ex_warrant_date', 'exercise_deadline')
    # def validate_dates(self, key, date_value):
    #     if date_value is None:
    #         raise WarrantValidationError(f"{key} cannot be None")
    #     return date_value

    def calculate_theoretical_warrant_value(self, market_price):
        """Calculate theoretical warrant value"""
        if market_price and self.exercise_price and self.warrant_ratio:
            cum_warrant_price = market_price
            ex_warrant_price = (cum_warrant_price + (self.exercise_price / self.warrant_ratio)) / (
                    1 + (1 / self.warrant_ratio))
            self.theoretical_warrant_value = cum_warrant_price - ex_warrant_price

    def calculate_intrinsic_value(self, market_price):
        """Calculate intrinsic value (immediate exercise value)"""
        if market_price and self.exercise_price and self.exercise_ratio:
            self.intrinsic_value = max(0, (market_price - self.exercise_price) * self.exercise_ratio)

    def __repr__(self):
        return (
            f"<WarrantExercise(id={self.corporate_action_id}, "
            f"exercise_price={self.exercise_price}, "
            f"expiration='{self.exercise_deadline}')>"
        )
