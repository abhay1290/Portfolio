from sqlalchemy import Column, Date, Float, ForeignKey, Integer, NUMERIC, Text

from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from equity.src.model.corporate_actions.model.CorporateActionBase import CorporateActionBase


class StockDividend(CorporateActionBase):
    __tablename__ = 'stock_dividend'
    __mapper_args__ = {
        'polymorphic_identity': CorporateActionTypeEnum.STOCK_DIVIDEND.value
    }
    API_Path = 'Stock-Dividend'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Stock dividend ratio
    dividend_shares_per_held = Column(NUMERIC(precision=10, scale=6), nullable=False)
    dividend_percentage = Column(Float, nullable=True)

    # Dates
    declaration_date = Column(Date, nullable=False)
    ex_dividend_date = Column(Date, nullable=True)
    distribution_date = Column(Date, nullable=False)

    # Valuation
    fair_market_value = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Fractional share handling
    cash_in_lieu_rate = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Tax implications
    taxable_value = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Metadata
    stock_dividend_notes = Column(Text, nullable=True)

    def calculate_dividend_percentage(self):
        """Calculate dividend percentage from shares per held"""
        if self.dividend_shares_per_held:
            self.dividend_percentage = float(self.dividend_shares_per_held) * 100

    def __repr__(self):
        return (
            f"<StockDividend(id={self.corporate_action_id}, "
            f"shares_per_held={self.dividend_shares_per_held}, "
            f"distribution_date='{self.distribution_date}')>"
        )
