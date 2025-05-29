from sqlalchemy import Column, Date, Float, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class SpinOff(CorporateActionBase):
    __tablename__ = 'spin_off'
    API_Path = 'Spin-Off'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Spin-off details
    spun_off_equity_id = Column(Integer, ForeignKey('equity.id'), nullable=False)
    distribution_ratio = Column(NUMERIC(precision=10, scale=6), nullable=False)  # New shares per old share

    # Dates
    announcement_date = Column(Date, nullable=True)
    ex_date = Column(Date, nullable=False)
    distribution_date = Column(Date, nullable=False)

    # Valuation and cost basis
    parent_cost_basis_allocation = Column(Float, nullable=True)  # Percentage
    spinoff_cost_basis_allocation = Column(Float, nullable=True)  # Percentage
    spinoff_fair_value = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Fractional share handling
    cash_in_lieu_rate = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Metadata
    spinoff_reason = Column(Text, nullable=True)
    spinoff_notes = Column(Text, nullable=True)
