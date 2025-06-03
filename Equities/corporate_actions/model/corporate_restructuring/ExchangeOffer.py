from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, NUMERIC, String, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase
from Equities.utils.Exceptions import ExchangeOfferValidationError


class ExchangeOffer(CorporateActionBase):
    __tablename__ = 'exchange_offer'
    API_Path = 'Exchange-Offer'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Exchange details
    new_security_id = Column(Integer, ForeignKey('equity.id'), nullable=False)
    exchange_ratio = Column(NUMERIC(precision=10, scale=6), nullable=False)
    cash_component = Column(NUMERIC(precision=20, scale=6), nullable=True)
    fractional_shares_handling = Column(String(50), nullable=False, default='ROUND')  # ROUND, PAY_CASH, FLOOR

    # Dates
    offer_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    settlement_date = Column(Date, nullable=True)

    # Conditions
    minimum_participation = Column(Float, nullable=True)
    is_voluntary = Column(Boolean, default=True, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)

    # Metadata
    exchange_terms = Column(Text, nullable=True)
    exchange_notes = Column(Text, nullable=True)

    # Calculated fields
    implied_premium = Column(Float, nullable=True)
    participation_rate = Column(Float, nullable=True)

    def calculate_implied_premium(self, new_security_price: float):
        """Calculate the implied premium based on new security price"""
        if not self.equity or not self.equity.market_price:
            raise ExchangeOfferValidationError("Original security price not available")

        implied_value = (self.exchange_ratio * new_security_price) + (self.cash_component or 0)
        self.implied_premium = (implied_value - self.equity.market_price) / self.equity.market_price

    def mark_completed(self, actual_settlement_date, actual_participation_rate: float = None):
        """Mark the exchange offer as completed"""
        self.settlement_date = actual_settlement_date
        self.participation_rate = actual_participation_rate
        self.is_completed = True

    def __repr__(self):
        return (f"<ExchangeOffer(id={self.corporate_action_id}, "
                f"ratio={self.exchange_ratio}, "
                f"cash={self.cash_component}, "
                f"completed={self.is_completed})>")
