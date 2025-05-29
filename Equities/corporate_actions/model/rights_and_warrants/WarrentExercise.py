from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class WarrantExercise(CorporateActionBase):
    __tablename__ = 'warrant_exercise'
    API_Path = 'Warrant-Exercise'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Warrant details
    exercise_price = Column(NUMERIC(precision=20, scale=6), nullable=False)
    exercise_ratio = Column(NUMERIC(precision=10, scale=6), nullable=False)  # Shares per warrant

    # Dates
    expiration_date = Column(Date, nullable=False)
    exercise_deadline = Column(Date, nullable=False)
    settlement_date = Column(Date, nullable=True)

    # Exercise conditions
    is_cashless_exercise = Column(Boolean, default=False, nullable=False)
    minimum_exercise_quantity = Column(Integer, nullable=True)

    # Valuation
    intrinsic_value = Column(NUMERIC(precision=20, scale=6), nullable=True)
    time_value = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Metadata
    warrant_terms = Column(Text, nullable=True)
    exercise_notes = Column(Text, nullable=True)
