from sqlalchemy import Column, Date, Float, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class StockDividend(CorporateActionBase):
    __tablename__ = 'stock_dividend'
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

    # @validates('dividend_shares_per_held')
    # def validate_dividend_ratio(self, key, value):
    #     if value is None or value <= 0:
    #         raise StockDividendValidationError("Dividend shares per held must be positive")
    #     return value
    #
    # @validates('dividend_percentage')
    # def validate_percentage(self, key, value):
    #     if value is not None and (value <= 0 or value > 100):
    #         raise StockDividendValidationError("Dividend percentage must be between 0 and 100")
    #     return value
    #
    # @validates('declaration_date', 'distribution_date')
    # def validate_dates(self, key, date_value):
    #     if date_value is None:
    #         raise StockDividendValidationError(f"{key} cannot be None")
    #     return date_value

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
